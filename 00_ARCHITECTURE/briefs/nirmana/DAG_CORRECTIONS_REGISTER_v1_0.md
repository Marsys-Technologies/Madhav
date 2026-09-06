---
artifact: DAG_CORRECTIONS_REGISTER_v1_0.md
canonical_id: NIRMANA_DAG_CORRECTIONS_REGISTER
version: "1.0"
status: OPEN — accumulates through the campaign; consumed at the NEXT definition freeze
produced_on: 2026-09-05
owner: CONDUCTOR
campaign_id: nirmana-elevation
definition_revision: t0-2026-09-01-0e5b06fb
authorized_by: >
  Conductor rulings D-CND-07 (the E-gate is only as sound as depends_on), D-CND-09
  (depends_on and layer are immutable inside a frozen definition; the definition is
  un-supersedable at 174+ events), and D-CND-10 (a cycle closed by something other
  than a DAG edge is a DELIBERATE NON-EDGE and must be recorded next to its guard).
mode: REGISTER — not a change request. Nothing here is applied this campaign.
---

# NIRMĀṆA — DAG CORRECTIONS REGISTER

## §1 — Why this exists, and why it is a register rather than a fix

The E-gate gates W4 on an asset's transitive `depends_on` closure. **It is therefore only as sound
as `depends_on`** — and L3 proved that array is wrong at L3, in both directions: **36 hidden edges
and 17 false edges across 23 assets** (`L3_DEPENDS_ON_AUDIT_v1_0.md`). A hidden edge opens a gate
that should be shut.

**The corrections cannot be applied.** Per **D-CND-09**, `depends_on` and `layer` are the two fields
pinned against the frozen manifest, and the definition is **un-supersedable** — it carries 174+
events and 11+ build runs, and `supersedeNirmanaElevationDefinition` refuses on either. So a
corrected `depends_on` in `asset_registry` makes the live fingerprint diverge and the dispatcher
refuses the asset.

That leaves exactly three legitimate responses, all of them already ruled:

1. **HOLD** the affected asset (D-CND-07) — a green E-gate is necessary, never sufficient.
2. **Enforce the missing edge by dispatch sequencing** — sequential single-asset `--assets`
   dispatches, per L1's workaround on #1744. Correctness by ordering rather than by declaration.
3. **RECORD it here**, so the next definition freeze inherits the correction.

**This file is response 3.** It is the only artefact that survives the campaign, and **the next
freeze is the only moment the fix is cheap.**

## §2 — Per-layer audit index

Each layer owns its own audit and publishes it as its own artefact; this register **indexes** them
rather than copying, so there is one authority per layer and no transcription drift.

| layer | audit artefact | status | headline |
|---|---|---|---|
| **L3 Kāla** | `L3_DEPENDS_ON_AUDIT_v1_0.md` | ✅ **COMPLETE** | 23/23 audited · CLEAN 7 · HIDDEN 4 · FALSE 7 · BOTH 5 · **36 hidden / 17 false edges** · 9 assets HELD under D-CND-07 |
| **L0 Brahmagyan** | — | ⬜ outstanding | 40 assets, 24 with zero declared deps |
| **L1 Gaṇita** | `L1_DEPENDS_ON_AUDIT_v1_0.md` | 🟡 IN PROGRESS | 12 confirmed findings (11 self-reported on #1744 + 1 new, `ga_yoga → ga_positions` hidden edge, Conductor-confirmed on #2180) · `ga_dashas → ga_vargas` hidden edge has a MEASURED live correctness consequence (build `6479bb56`, concurrent start, MVCC stale read) · not yet a systematic per-asset grep sweep like L3's (own §3 names the gap) |
| **L2 Bodha** | — | ⬜ outstanding | 22 assets, avg 3.1 declared deps |
| **L4 Phala** | — | ⬜ outstanding | 9 assets, avg 4.6 declared deps |
| **L5 Mīmāṃsā** | — | ⬜ outstanding | 15 assets, 2 with zero declared deps |

**L3's method is the model** and the other five should copy it rather than invent one: pull the
declared side from `asset_registry`, build the owner map `target_table → asset_id`, then grep each
writer's real SQL for `\b(from|join|update|into|delete from)\s+<table>\b` against the live table
universe, longest-match-first. It reports **both** directions and states what the method cannot see.

## §3 — DELIBERATE NON-EDGES (D-CND-10)

**Pairs where an edge looks missing and must NOT be added.** This section exists because a register
that only lists *missing* edges invites the very edit it is meant to prevent: the next competent
person doing dependency hygiene adds the "obvious" edge and breaks the build.

### 3.1 `ka_kshetra` ↔ `mi_bhara` — closed by version pin, not by edge

There is a genuine `ka_kshetra → mi_bhara → ka_kshetra` cycle. It is closed by a **version pin**
(`kala_field_weight_versions`), **not** by a DAG edge, because a DAG edge would make `topoSort`
reject every plan containing both assets.

**Adding either edge breaks every plan containing either asset — not just this campaign's wave,
every future chart build.**

* Documented at `services/mi_bhara/weights.py:14-30`.
* Positively asserted by `assert_no_weights_cycle`, which checks both that
  `'mi_bhara' NOT IN ka_kshetra.depends_on` **and** that a plan containing
  `{ka_kshetra, mi_bhara, mi_sankalpa}` topo-sorts.
* Arbitrated on issue #1743: `kala_field_weight_versions` and `kala_field_weights` are **L3-owned**;
  L5 reads only; both fenced for the campaign.

**Guard to preserve:** `assert_no_weights_cycle`. If a future freeze adds this edge, that assertion
is what will fail — keep it.

## §4 — How the next definition freeze consumes this

1. Read §2's per-layer audits and apply every **hidden** edge and remove every **false** edge in the
   new manifest's `depends_on`.
2. Read §3 and **do not** add any listed non-edge; verify each named guard still exists.
3. Re-derive `registry_fingerprint_sha256` for every changed asset — the fingerprint includes
   `depends_on`, so every correction moves it, and that is expected at a freeze rather than a defect.
4. Only then freeze. **A freeze that skips step 2 will pass its own self-consistency check and break
   `topoSort` at the first build.**

## §5 — Open items owed to this register

* **Five layer audits** (§2) — L0, L1, L2, L4, L5.
* **Deliberate non-edges from the other layers** — §3 currently holds one entry, contributed by L5
  and L3 jointly. Any pair closed by a version pin, a resolve-once rule, or a staged read belongs
  here.
* **L3's two no-FK referrers of `kala_convergence`** — `bodha_convergence.convergence_id` (uuid,
  against L3's `bigint` key, so possibly not a live pointer at all — L2 to confirm rather than
  assume) and `kala_convergence_staging.convergence_id` (bigint, L3's own). Not DAG edges, but the
  same class of undeclared coupling and they will matter to the next freeze.
