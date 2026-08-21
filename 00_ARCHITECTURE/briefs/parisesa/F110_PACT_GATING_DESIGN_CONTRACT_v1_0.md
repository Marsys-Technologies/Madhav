---
canonical_id: F110_PACT_GATING_DESIGN_CONTRACT
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-110 (CL-15 Cross-tool incoherence — TIER1-CORRECTNESS, top-severity)
lane: LANE-PROMISEGATE (CL-15)
authored: 2026-08-21
authority: GA-2 design authority (PARIŚEṢA-V4)
native_ruling_required: YES — §7 (Option B/D escalation only). §5 (Option C) is
  implemented under existing doctrine and needs no new ruling.
---

# F-110 — PACT Gating for `tier_1_high` Confidence Laundering

## §1 — The finding, restated precisely

For the identical chart (`482012f1-710e-4a25-994a-93821f5871aa`, Abhisek Mohanty),
identical domain (`relationship`) and identical evaluation date, the MCP fleet serves two
irreconcilable verdicts, and **which one a real person receives is decided entirely by
which tool the consuming LLM happens to pick**:

| Path | Verdict | Narration |
|---|---|---|
| `kala_ahead_get(domain='relationship', horizon_years=10)` | `projections[0].probability_tier = "tier_1_high"`, window `2027-10-20..2030-04-03` | "High probability (>=70% convergence, clear activation). Effective convergence: 0.70." |
| `pact_query` / `kala_upaya_get(domain='relationship')` | `pact_status = "denied_at_promise"`, composite `-3.5`, grade `contested` | "The rāśi checklist does not promise this matter … no later stage can deliver what the rashi itself does not promise" |

The natural tool for "when will I marry" is the one that omits the denial.

### 1.1 — Live re-reproduction (current `main`, 2026-08-21)

Re-run on `main` @ `cfef54a`, live production MCP, canonical chart:

- `kala_ahead_get` → `probability_tier: "tier_1_high"`, `max_effective_score: 0.7`,
  `reading.evidence[0].strength: "strong"`, `reading.dissent: []`,
  `reading.verdict.statement: "1 high, 0 moderate, 0 speculative forward window(s) …"`,
  and — naming its own gap in its own coverage block —
  `{"concept":"promise_gated_forecasting","state":"not_in_corpus","reason":"Law-3 PACT
  gating (\"pressure without delivery\") is not yet applied to these raw windows …"}`.
- `pact_query(domain='relationship', as_of_date='2026-08-15')` → `pact_status:
  "denied_at_promise"`, `stages: [{stage:"PROMISE", status:"denied", verdict_grade:
  "contested", composite_score:-3.5}]`, `grounding.fact_ids` = **63** resolvable L1 facts
  including `d332fe1dbda74ea0`.
- `kala_upaya_get(domain='relationship')` → `diagnosis.pact_status: "denied_at_promise"`,
  `failing_link: "promise"`.

**F-110 is CONFIRMED-CURRENT, not a historical artifact.** `current_evidence_freshness`
in the corpus ledger moves UNKNOWN → CONFIRMED-2026-08-21.

## §2 — The laundering mechanism, exactly

The name "confidence laundering" is precise. Three distinct things happen, and only the
third is the launder:

1. **L3 `ka_bhavishya_lekha` computes a convergence score of 0.70** for a relationship
   signal family and grades it `tier_1_high`. This is a *convergence* measure — how many
   temporal signals point at the same window — and it is honest at its own layer. L3 never
   claimed the event is promised; it claimed signals converge.
2. **`kala_ahead_get` reads that tier verbatim** and re-presents it. Reading verbatim is
   correct and doctrinally mandatory (§N.5: L1/L3 is the authority; the serving layer must
   never restate a computed value as its own). Its own file header states the contract:
   *"probability_tier is read verbatim from kala_bhavishya, never re-graded."*
3. **`kala_ahead_get` then narrates that tier in its OWN prose** as `strength: "strong"`,
   thesis *"leading: relationship (high probability, window …)"*, verdict *"1 high, 0
   moderate, 0 speculative"*, and `dissent: []` — **while the same server holds, on 63
   cited L1 facts, a classical verdict that the matter is not promised at all.**

Step 3 is the launder. A *convergence* number (0.70 of signals agreeing) is re-narrated,
by a layer that authored the sentence itself, as a *probability of the event* ("High
probability", "strong", "clear activation"), with the denial nowhere in the envelope.
The `dissent: []` is not an absence of dissent — it is an assertion that none exists.

`assess_marriage`'s `contradictions.status = 'no_contradictions_in_domain'` compounds it:
an active certification of absence-of-tension in the exact domain the promise chain
denies. (INV-1 in `promise_spine.ts` already declares this certification illegal.)

### 2.1 — The gap is *known* and *named* by the code that has it

`ahead.ts:1862` emits an unconditional `not_in_corpus` coverage row for
`promise_gated_forecasting`. That is honest disclosure of a build gap — and it is also
**a permanently-hardcoded string with no detector behind it**. It cannot ever read
anything else, no matter what the PACT chain says. Per §N.8 (Earned-Signal Principle) a
status with no code path that could produce a different value is not a status.

### 2.2 — The helper already exists and has ZERO production callers

`platform-mcp/src/lib/promise_spine.ts` exports `interpretPactJoin(raw) →
SaraPromiseJoin | null` — a pure, fully-tested function that maps any `denied_at_*`
`pact_status` to `projection:'contradicted'` / `stance:'contradicts'`, with **no override
path** (its own comment: "INV-1 enforcement: denied_at_* → 'contradicts' (no override
path)"). It has a 200-line test file.

`grep -rn interpretPactJoin --include='*.ts'` over the whole repo returns **only
`promise_spine.ts` itself and `promise_spine.test.ts`.** No production code calls it.

Worse, the module's own header states as fact: *"registry_bridge.ts assess_\* handlers
wire it in by calling `interpretPactJoin` in parallel with their main capability call."*
**They do not.** `assess_marriage`/`career`/`health`/`wealth` (`registry_bridge.ts`
~3125–3260) call `fetchOrientationContext` + `callRegistryCapability` +
`attachDomainCompleteness` + `attachDomainReading` — and nothing else. The docstring is a
claim about code that was never written: an §N.8 defect in the very module authored to fix
an §N.8 defect.

**So: is F-110 a straightforward wiring fix?** Half of it. The *mapping* is built,
correct, and tested. The *policy* — what a `contradicts` stance is permitted to do to a
served `tier_1_high` — is genuinely undecided, and the two obvious answers both violate
standing doctrine. §3–§5 resolve that.

## §3 — Why the two obvious fixes are wrong

### 3.1 — Option A: downgrade the tier (`tier_1_high` → `tier_2`/`tier_3`/null)

**Rejected.** Three independent failures:

- **§N.5 violation.** `probability_tier` is an L3-computed value. A serving facade that
  rewrites it makes the facade an authority over its own substrate — the exact
  computed-value authority inversion documented in
  `MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md` and the trap L2+ is explicitly forbidden to
  repeat. `ahead.ts`'s own header contract ("never re-graded") would become false.
- **§N.8 violation.** *Which* lower tier? Any mapping (→`tier_2_moderate`?
  →`tier_3_speculative`? →`null`?) is a number invented at the serving layer with no
  detector measuring it. The convergence really is 0.70; writing 0.4 because a different
  question was answered "no" is fabrication dressed as caution.
- **Category error.** The tier measures *signal convergence*; PACT measures *classical
  promise*. They are not the same axis, so one cannot arithmetically correct the other.
  Collapsing them destroys the ability to say the genuinely interesting thing: **strong
  temporal pressure on a matter the rāśi does not promise** — which is precisely Law-3's
  "pressure without delivery" and is diagnostic information, not noise.

### 3.2 — Option B: block/suppress the projection

**Rejected as default; escalated in §7 as a possible audience-tier policy.**

- **B.10 violation.** Never silently drop computed data.
- **§N.6 item 1 violation.** The prescribed handling of a lower-trust row is *serve it,
  count it separately, flag it* — never delete it.
- **Overclaims the denial.** `denied_at_promise` here is a `contested` composite of
  `-3.5`, and `pact_query`'s own drill pointer says so: *"the composite denial may still
  merit a manual bhaṅga check."* A contested composite is a strong classical judgment, not
  a proof of impossibility. Suppression would launder confidence in the *opposite*
  direction — presenting a contested denial as settled fact by erasing the counter-evidence.

## §4 — The two axes the fix must separate

The correct fix rests on a distinction the current code does not make.

### 4.1 — Axis 1: whose sentence is it?

| Field | Author | May the fix change it? |
|---|---|---|
| `projections[].probability_tier` | L3 `ka_bhavishya_lekha` | **NO** — §N.5, verbatim |
| `projections[].narrative.*` ("High probability (>=70% …)") | L3, verbatim | **NO** — §N.5 |
| `projections[].max_effective_score` | L3 | **NO** — §N.5 |
| `reading.thesis` / `reading.verdict.statement` / `reading_prose` | **`ahead.ts` itself** (`buildAheadReading`) | **YES** |
| `reading.evidence[].strength` | **`ahead.ts` itself** (`TIER_TO_STRENGTH`, ahead.ts:1128) | **YES** |
| `reading.dissent` | **`ahead.ts` itself** — currently hardcoded `[]` | **YES** |
| `coverage[promise_gated_forecasting]` | **`ahead.ts` itself** — hardcoded `not_in_corpus` | **YES** |

**This is the load-bearing insight.** The tier is L3's to state and must pass through
untouched. But `TIER_TO_STRENGTH['tier_1_high'] = 'strong'`, the thesis sentence, and
`dissent: []` are `ahead.ts`'s own compositions — §N.7 (Narration Fidelity) governs them,
and §N.7 item 6 is explicit: *an honest null beats an invented judgment*. `ahead.ts` may
not author the word "strong" and the empty array `dissent: []` while holding a
contradicting classical verdict on 63 cited facts. **Fixing the narration is not
re-grading the tier.**

### 4.2 — Axis 2: is the denial horizon-invariant?

A naive wiring would apply *any* `denied_at_*` to *every* forward window. That is wrong,
and getting it wrong would create a second correctness defect while fixing the first:

| `pact_status` | Rests on | Valid gating scope |
|---|---|---|
| `denied_at_promise` | natal rāśi checklist — timeless | **horizon_invariant** — gates every forward window in the domain |
| `denied_at_confirmation` | varga dignity of the promise-carrier — timeless | **horizon_invariant** |
| `denied_at_activation` | which daśā runs **as of one date** | **as_of_date_only** — says nothing about a window in 2030; must NOT gate it |
| `chain_pending_activation` | activation not yet reached | **none** — not a denial |
| `chain_incomplete_infra` | ephemeris sidecar gap | **none** — infrastructure, not classical (R-22) |
| `chain_complete` | all four stages | **none** — corroborates |

A PROMISE/CONFIRMATION denial is a statement about the chart. An ACTIVATION denial is a
statement about a date. Only the first may be carried across a 10-year horizon.

## §5 — RECOMMENDATION: Option C — adjacent reconciliation, not tier surgery

**Serve the L3 tier and narrative byte-identically. Add the denial as a first-class,
machine-readable, adjacent field. Correct `ahead.ts`'s OWN narration so it stops asserting
a consensus it does not hold. Replace the hardcoded coverage lie with a real detector.**

This is the §N.6 Serving Density Principle applied exactly as written: differing-density
layers served side by side, never flattened; the lower-trust reading counted and flagged
separately with a pointer to the authoritative surface; and no section silently emptied.

### 5.1 — What ships (implemented on this branch)

1. **`interpretPactJoin` gains its first production caller.** `ahead.ts` calls
   `marsys://tool/L-PACT/pact_query` (the SAME capability `pact_query`/`kala_explain_get`
   consume — no second implementation, no new astrological computation) and passes the raw
   result through `interpretPactJoin` verbatim.
2. **New response field `promise_gate`**, three honest states — `checked` /
   `unreachable` / `not_applicable` — carrying the `SaraPromiseJoin`, the verbatim
   `pact_status`, the §4.2 `gating_scope`, `gated_projection_domains[]` vs
   `ungated_projection_domains[]` (§N.6: never flatten "vetted" and "not vetted"), and a
   `contradicts_served_projections` boolean.
3. **`reading.dissent` populated** with the PACT denial, `source: 'PACT promise chain
   (pact_query)'`, carrying the denial's own fact_ids — closing the `dissent: []`
   assertion-of-no-dissent.
4. **`reading.thesis` + `reading.verdict.statement` + `reading_prose` state the
   contradiction inline**, naming the drill instrument. A caller reading only the prose can
   no longer miss it.
5. **`evidence[].strength` for a contradicted projection becomes `undefined`, not
   `'strong'`.** `undefined` is already the codebase's own established value for
   ungraded evidence (`ahead.ts:1538` emits it whenever `probability_tier` is null) — this
   is §N.7 item 6's honest null, **not** an invented lower grade. The tier itself is
   untouched and still says `tier_1_high` two fields away.
6. **The `promise_gated_forecasting` coverage row gets a real detector** — `computed` when
   a chain was actually consulted, `honest_empty` when the capability was unreachable,
   `not_in_corpus` **only** in the genuinely-unbuilt case. This retires the §N.8 defect at
   `ahead.ts:1862`.
7. **`interpretPactJoin`'s false docstring corrected** — it now names its real caller
   instead of a wiring that was never written.

### 5.2 — Honest interim disclosure (the baseline, per task item 6)

The `not_applicable` / `unreachable` states are the deliverable that matters most even if
§7 is never ruled on. **A `tier_1_high` verdict that has not been checked against PACT now
says so, in a machine-readable field, on every call.** Before this branch, "checked and
clear" and "never checked" were byte-identical to a caller. They are now distinguishable.

### 5.3 — Deliberate scope limits (stated, not hidden)

- One PACT call per response, scoped to `args.domain ?? leading projection's domain`.
  `pact_query` runs `judgment_query`'s full checklist and is expensive; N parallel heavy
  calls on every `kala_ahead_get` is an unacceptable latency regression. Projections in
  *other* domains are listed by name in `ungated_projection_domains` — honestly disclosed
  as unvetted, never implied clean.
- `assess_marriage`'s `no_contradictions_in_domain` (INV-1 breach) is **not** fixed here.
  It is a `registry_bridge.ts` change on the L-DOMAIN capability path, a separate blast
  radius. Carried as **residual F-110-b**.
- `kala_windows_get` / `kala_projections_get` serve the same substrate un-gated. Carried
  as **residual F-110-c**.

## §6 — Acceptance criteria

| # | Criterion | State |
|---|---|---|
| A1 | `interpretPactJoin` has ≥1 production caller | MET |
| A2 | `kala_ahead_get(relationship)` on the canonical chart emits `promise_gate.pact_status = 'denied_at_promise'` | MET (unit); live pending deploy |
| A3 | `reading.dissent` non-empty when the chain contradicts | MET |
| A4 | `probability_tier` + `narrative` byte-identical to pre-fix | MET (asserted by test) |
| A5 | `denied_at_activation` does NOT gate a forward horizon | MET (asserted by test) |
| A6 | `promise_gated_forecasting` coverage varies with real input | MET (asserted by test) |
| A7 | Unchecked ≠ clean — distinguishable by a caller | MET |
| A8 | Live post-deploy re-run of the §1.1 reproducer | **OPEN** — requires deploy |

## §7 — What still needs a native ruling (escalated, NOT decided here)

Option C makes the contradiction impossible to miss for any caller that reads the
envelope. It does **not** decide these three, which are policy, not engineering:

- **R1 — Should a horizon-invariant denial ever *suppress* a `tier_1_high` projection for
  a `native_self` audience tier?** Option C says no (B.10/§N.6). A native asking "when
  will I marry" and receiving a dated window plus an adjacent denial is better served than
  one receiving either alone — but that is a duty-of-care judgment about a real person
  reading a real marriage prediction, and it belongs to the native, not to GA-2.
- **R2 — Should L3 `ka_bhavishya_lekha` itself consume PACT at build time**, so
  `probability_tier` is promise-gated *at the layer that owns the number* rather than
  reconciled at serve time? This is the architecturally cleaner fix and the only one that
  can legitimately change the tier (§N.5 permits the owning layer to grade its own value).
  It is an L3 writer change against a CLOSED layer seal and needs its own campaign.
- **R3 — Does INV-1 bind `assess_*` (residual F-110-b)?** `promise_spine.ts` asserts INV-1
  as an invariant ("no caller may certify 'no contradictions' for a classically-denied
  domain"), but no code enforces it on the `assess_*` path — itself an §N.8 pattern: an
  invariant with no enforcer.

**Until R1/R2 are ruled, Option C is the correct floor: the system may not know which
verdict is right, but it must never again present one while silently holding the other.**

---

*F110_PACT_GATING_DESIGN_CONTRACT v1.0 — PARIŚEṢA-V4, GA-2 design authority, 2026-08-21.*
