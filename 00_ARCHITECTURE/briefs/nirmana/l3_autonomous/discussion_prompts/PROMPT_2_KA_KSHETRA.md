# FOCUSED ELEVATION DISCUSSION — ka_kshetra

You are opening a **dedicated design discussion** with the native (Abhisek Mohanty) about
`ka_kshetra`, the largest and most complex asset in L3 Kāla. **This is a discussion, not an
execution session.** Do not write production code, do not dispatch builds, do not rebuild
anything. Your deliverable is one reviewed brief.

## Read first

- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` — §3 (the data
  contract), §5 + the P0–P6 table, §6.1 row L3-A22, **§6.2 in full** (Kshetra's data families and
  internal stage DAG)
- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md`,
  `..._W0_FIELD_CONTRACT_REGISTER_v1_0.md` (39 partitions / 699 fields),
  `..._DHARA_NUMERICAL_CONTRACT_v1_0.md`
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` — §1, §2
  Tier S, §5 Q4
- Code: `services/ka_kshetra/**` (14,113 LOC non-test + 4,465 own tests), especially
  `dhara_null_vec.py`, `layer1.py`; `pipeline/transit_search.py`

## The measured situation — verify before relying on it

**Scale.** 14,113 LOC — more than the next ten L3 assets combined. Eighteen internal relations:
`kala_field`, `_kinematics`, `_promise_nodes`, `_promise_edges`, `_routes`, `_clocks`,
`_clocks_digest`, `_boundaries`, `_primitives`, `_null`, `_windows`, `_provenance`, `_salience`,
`_weights`, `_weight_versions`, `_snapshots`, plus `kala_insights` and `kala_timeline_spec`.

**Internal DAG** (stage names are not execution order):
`S0 kinematics` and `S2 structure/routes` have independent prerequisites → `S3 clocks/boundaries`
→ `S1 primitives` → `S4 field` → `S5 null/windows/provenance` → `S6 salience` → `S6.5 insights`
→ `S8 timeline` → complete snapshot. **A partially completed stage set cannot be selected as a
complete snapshot.**

**Three facts that should shape the discussion:**

1. **~8.6M rows already written for the canonical chart, while a served surface hard-codes
   "field empty"** (recorded as PARK-5 by an earlier campaign, deliberately left unfixed as
   out-of-scope). Separately, `kala_field_snapshots` has **zero rows** for that chart — the field
   snapshot has never been built. Establish what those 8.6M rows actually are and whether they
   satisfy any part of the field contract.
2. **It carries four of the seven performance items** — P0 (planner safety), P1 (the DHARA null
   programme: ~372M scalar sliding-window differences and ~37M heap visits per class at the
   inspected century/replicate settings), P2 (shared context/sweep), P6 (publication).
3. **Ownership boundary.** Kshetra owns only `kala_insights.lel_derived = false`; `mi_bhara`
   owns the true side. The accepted L2 cross-layer delete guard deliberately refuses unsafe
   deletion and **must not be disabled to get a rebuild through**.

## What the discussion must settle

1. **Q4 from the elevation plan — is the continuous-field model the right abstraction to
   preserve?** This is the single largest investment in the layer. Before paying for P1's exact
   blocked order-statistic work, confirm the field is something the native actually wants to
   consume, and in what form. If it is, say why. If it is not, say what replaces it.
2. **What is `kala_field` *for*, in the native's own terms?** Which product question (L3-Q01–Q13)
   does the continuous field answer that a discrete window ladder cannot?
3. **PARK-5 — is the served surface wrong, or is the data unusable?** 8.6M rows and a hard-coded
   "field empty" cannot both be right. Which is the defect?
4. **The null programme.** `kala_field_null`'s p/R statistics are explicitly **not** empirical
   event probability. Agree what they *do* mean, what the honest denominator is, and what
   independent numerical oracle validates them — the old output is not the oracle where the
   method has a defect.
5. **Staged acceptance.** Is Kshetra one terminal asset, or does each stage family earn its own
   acceptance? The strategy treats it as "a staged data system, not one opaque writer" and gives
   it an internal W2–W7 DAG. Decide how `Accepted N/22` counts a partially-elevated Kshetra —
   it is one of the 22 either way.
6. **Resume and publication semantics.** Resume signatures must invalidate only genuinely changed
   dependencies and must prevent an old late worker publishing over a newer accepted generation.
   Confirm the intended behaviour before the mechanism is built.
7. **Which of the 699 registered fields are load-bearing** versus retained-but-unused? Every
   material field needs a receiving operator and a falsifying test (elevation plan D1); the
   register is the worklist, not a summary.

## Deliverable

`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/BRIEF_KA_KSHETRA_v1_0.md`, containing:

- Qualified purpose of the continuous field in the native's terms, and the product questions it
  serves
- Per-family (§6.2) field/producer obligations and the structure that must survive
- The native's ruling on each numbered question, rationale included, open items named
- The PARK-5 disposition
- The staged-acceptance decision and how it maps to `Accepted N/22`
- The null-statistic semantic contract and its independent oracle
- A P0/P1/P2/P6 sequencing position — what must be true before expensive rebuild trials
- What is **not** settled

## Conduct

Ground every claim in file, line or live query; prefer aggregate queries over sampling private
chart content. Do not disable or weaken the cross-layer delete guard, and do not treat its refusal
as an obstacle — it is the protection working. Where a method lacks qualification, route it to its
authority rather than inventing doctrine. If the honest answer to Q1 is "we do not yet know
whether this is worth preserving", say that.
