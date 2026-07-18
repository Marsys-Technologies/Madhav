---
artifact: MEMO_D-3_1
type: HALT-AND-REPORT DECISION MEMO (ESCALATION_POLICY_v1_0.md §2)
wave: D-3 — Kāla Taraṅga + Three-Lock
cycle: 2b
trigger_class: "§2.1-adjacent — the scientific-integrity gate (§G) is rendered uninformative/un-exercisable by a newly-discovered pre-existing bug; the Opus Adjudicator ruled it may not decide whether a §G result under this condition counts as campaign evidence (CHARGE §4), and routed the sequencing decision to the native per ESCALATION §2"
status: blocked
authored_by: Sonnet conductor session, 2026-07-18
---

# MEMO_D-3_1 — §G gate blocked: TRIGGER cannot fire on Abhisek's chart

## What happened

D-3 cycle-2b (T-4 PERMISSION, T-5 TRIGGER, ADMIT kernel-admission loop, hotfix-kakshya-401, T-6
serving) shipped clean: all 5 lanes independently Opus-verified ACCEPT, cross-lane integration
sweep clean (933 tests), PR #604 merged (`c40b56c2`), deployed live, kakṣyā-401 fix live-confirmed
working. Abhisek's chart (482012f1) was then rebuilt (run `818faf3a`, `ka_sangam` + L3/L4/L5
cascade, completed cleanly, no errors — all confirmed by direct Postgres query, not agent claim
or UI).

While validating that the rebuild actually reflects this cycle's work (CR-96 discipline — verify
the consuming surface, not the database, and a lane's claim ≠ served reality), I queried the
served `kala_convergence` table directly and found:

**100% of 1,580 post-rebuild rows are `mode: "C"` (the SUBSYSTEM/Mode-C ingress path). Zero rows
are Mode A or Mode B — the ONLY two code paths TRIGGER suppression and the CR-102 vedha fix are
wired into.** Confirmed via `constituent_factors`: 0 of 1,580 rows carry the
`trigger_weights_used`/`trigger_suppressive_applied` keys `apply_trigger_suppression()` writes on
a genuine fire.

## Root cause (traced from source, not inferred)

`ka_sangam.py::plan_substeps()` loads predicates via:
```sql
ORDER BY s.dignity_score DESC NULLS LAST, p.id ASC LIMIT 200   -- near tier (60 for lifetime)
```
`SUBSYSTEM`-classed predicates route to Mode C; everything else (`DISPOSITOR_RELATIONAL`,
`DIGNITY`, `DOSHA`, `YOGA`, `CLASSIFY_RESIDUAL`) routes to Mode A + Mode B.

All 6 signature classes have real, populated `dignity_score` (avg 0.50–0.57 across classes — this
is **not** a stub-predicate/NULL-score problem T-5's earlier audit already flagged). The actual
mechanism: **4,441 predicates across all classes are tied at the exact maximum `dignity_score =
1.0`** (SUBSYSTEM 3,827 / DISPOSITOR_RELATIONAL 552 / DIGNITY 60 / YOGA 2). With `LIMIT 200` inside
a 4,441-way tie, the `p.id ASC` secondary sort decides — and SUBSYSTEM predicates were inserted
with systematically lower `id` values (min 2,772,174) than DISPOSITOR_RELATIONAL (2,780,056) or
DIGNITY (2,812,374). SUBSYSTEM deterministically wins every near-tier and lifetime-tier slot for
this chart, every rebuild, under current code.

**This is PRE-EXISTING, not caused by D-3.** `plan_substeps()`'s predicate-loading SQL and the
Mode-C-vs-A/B routing predate cycle-2b entirely. T-6's diff only added `apply_trigger_suppression()`
calls *inside* the existing Mode A/B branches — it never touched predicate selection. This is a
newly-discovered defect this session found while validating the rebuild, not a regression any lane
introduced.

## Why this blocks §G

D-3's §G gate exists to test whether this cycle's kernel work — specifically TRIGGER, since T-4's
PERMISSION was admission-rejected — measurably improves retrodiction against Abhisek's Life Event
Log. TRIGGER cannot fire on the actual served data for this chart at all, under any rebuild, until
this predicate-selection bug is fixed. Running §G now would silently test the v1 baseline (+
whatever Mode-C-path effects already existed) and let a pass or fail be read as evidence about
TRIGGER when TRIGGER never executed.

## The Adjudicator's ruling (Opus, engineering seat, full reasoning in `STATE_D-3.md`)

Applied CHARGE §1 (confirmed via independent source re-derivation, not report-reading; confirmed
this is a newly-discovered defect not a regression per §1.2). Ruled the bug **is on the critical
path** and that **running §G as-is is FORBIDDEN**, not merely disfavored — doing so would launder a
baseline result into kernel evidence, the exact failure mode the campaign's Adjudicator charge
governing principle exists to stop. Then identified that deciding **whether §G's informativeness
can be sacrificed or must be restored before it counts as evidence** is itself reserved to the
scientific-integrity gate boundary (CHARGE §4 — "you may never adjudicate... the scientific-
integrity gate... if you find yourself reasoning toward why a marginal or red gate is 'really' a
pass, STOP") — and routed that specific decision here, to the native, per ESCALATION §2.

## Options for native disposition

**(A) Run §G as-is, disclosing the caveat.** — **The Adjudicator ruled this FORBIDDEN**, not just
disfavored. Included for completeness only; not a live option absent overriding the ruling.

**(B) Halt D-3 here; defer the TRIGGER-retrodiction test to a future wave.** Cycle-2b's work
(TRIGGER, CR-102 fix, PERMISSION, kernel-admission loop, kakṣyā-401 fix) stays merged and deployed
— it is correct and independently verified, just not yet exercised for this chart. The
predicate-selection bug becomes a tracked register defect (CR-N, native-side allocation) for a
later wave. D-3 closes without a positive TRIGGER-retrodiction proof this cycle.

**(C) Scope a new predicate-selection fix lane now**, re-run the L3 rebuild, then run §G. The
Adjudicator's provisional lean. Concretely: diversify the top-200/60 predicate selection across
signature classes (e.g. a per-class quota, or a different tiebreak that doesn't structurally favor
insertion order) so Mode A/B predicates — and therefore TRIGGER — get a chance to fire on real
data. This is genuinely out of D-3's declared T-0…T-6/ADMIT lane map (predicate selection was never
any lane's scope) and adds a full implement→verify→integrate→deploy→rebuild cycle before §G can
run.

**(D) Other** — native may propose a different path (e.g., a synthetic/targeted test proving
TRIGGER's mechanism correctness without waiting for natural predicate-selection diversity, if that
would satisfy the campaign's evidentiary bar without a full fix-and-rerun).

## Falsifier (what would reopen this without native input)

If a fresh `kala_convergence` query for 482012f1 ever shows ANY Mode A/B row bearing
`trigger_weights_used` (i.e., TRIGGER genuinely fired on real data), the "cannot test TRIGGER"
premise collapses and Option A becomes live again — the conductor should re-check this before
assuming the block still holds if resuming after any intervening change. Likewise, if the register
already carries a supersession disposition on predicate selection (ruling it dead code slated for
replacement), Option C flips to wrong-direction and B becomes the clear path.

## State at halt

- D-3 cycle-2b: fully shipped, deployed, verified — not in question.
- Abhisek's chart: rebuilt cleanly, `818faf3a`, no errors.
- All cycle-2b lane worktrees/branches: cleaned up already (merged-lane cleanup already ran per
  ESCALATION §0).
- No further D-3 work proceeds until this memo is dispositioned.

See `STATE_D-3.md` for the full ledger (`cycle2b_critical_finding_predicate_selection_bug`) and the
Adjudicator's complete ruling text.
