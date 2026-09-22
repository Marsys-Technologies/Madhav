---
artifact: KALA_ELEVATION_PROMPT_GOCHARA_FAMILY
version: "2.0"
status: READY_TO_PASTE
date: 2026-09-22
instantiates: KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md for the Gochara family (group shape)
scope: stages 0–2; terminal PROPOSED_FOR_NATIVE_RULING
---

You are elevating the **Gochara family** as a *group*: `ka_gochara_resonance`, `ka_gochara`,
`ka_gochara_v3_century_materialize`, `ka_vedha_gochara`, `ka_moorti_nirnaya` (+ `ka_kota_chakra`
as a proposed-use member) and the retired `ka_gochara_sweep` as protected history. Your scope is
**stages 0–2** of `KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md`: reconcile, frame the value, and
produce the brief. Stop at `PROPOSED_FOR_NATIVE_RULING`. Base branch is **`main`**; read files
not yet on `main` with `git show origin/l3/kala-elevation-readiness:<path>`.

## Read, in this order
1. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md` (all) and
   `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_INSTANTIATION_GUIDE_v1_0.md` §2–§12 (the brief's shape).
2. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/W0_DELTA_GOCHARA_FAMILY.md` and `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md`.
3. Your own `l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md` + Astra review + `evidence_gochara/`.
4. `briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §3 (**Contact** and **Search coverage**
   objects), §5 row **P3**, §6.1 rows A05/A06/A08/A13/A14/H01, §6.3.
5. `briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md` — census #4/#5/#6/#13/#20; fences 1–3.
6. `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` — the three served tools.

## The family's value proposition (stage 1)
Kāla's distinctive contribution is *"actual contacts, intervals, recurrence, trajectories"*
(Product §3.10). This family is the layer's **contact geometry** — the one place chart-relative
transit contacts are computed at all. VA §6.4 names the chain it must keep distinct: *raw celestial
motion → chart-relative contacts → eligible activation → convergence/comparison → publication.*
The Strategy §3 **Contact** object is what a consumer needs from you: *moving body, target
identity/frame, contact type and qualified orb, applying/separating/station/retrograde branch,
brackets/root time, numerical tolerance, source and coverage.*

## What is physically there, measured — and what is missing (stage 1, lens 2.1/2.2)
- `kala_gochara_windows_v2` has **23 fields and zero of the Contact object's geometry**: no
  applying/separating, no station/retrograde branch, no orb, no bracket or root time, no
  tolerance, no coverage. It stores *interpretive windows* at **DATE** grain (`window_start`,
  `peak_date`: DATE) with `signed_intensity`, `valence`, `term_breakdown` and credible-interval
  bounds. The contacts that produced them are **computed and discarded** (register class *b*).
  That is the family's single largest latent-value loss: the product's only contact engine keeps
  no contacts.
- **The served product is not `ka_gochara`'s output.** The three tools (`gochara_activation_get`,
  `gochara_election_avoidance_get`, `gochara_forecast_get`) read `kala_gochara_windows` filtered by
  `kala_gochara_authority.authoritative_generation` — live value **`3.0`** for the canonical chart
  (914 century-v3 rows). `ka_gochara` writes generation **2.0 into `_v2`** (87 rows) and **nothing
  serves them.** The member eligible for W2 produces what the product does not read; the member
  the product reads is the held materialiser. Your brief must decide, explicitly, **which member
  owns the served product** and what the authority pointer means after elevation.
- The registry `target_table` for `ka_gochara` was known and **held** at W0 (CURRENT_STATE
  §4.1:133); the Clear-route deletion path to `generation='v1'` (38,287 protected rows) was **not**
  known and is being closed by the Phase 1 session. Your brief depends on that closure.
- Declared Kota/Tithi→century edges are **not proven consumption** (§4.1, §6.3). Sangam reads the
  Gochara **service**, not the materialization. Vedha is read by century and, undeclared, by Sangam.

## Efficiency with quality (lens 2.3) — the P3 candidate, and the century decision
Strategy §5 **P3**: context reloaded per class×decade, scalar JD loop, overlapping primitive
searches, per-instant period scans → *"unique target-specification events over absolute intervals
plus boundary halos; chart/common and class-specific context; time-indexed clocks; batched
hierarchy writes."* Equivalence: *"no missing narrow/station/retrograde events; complete boundary
joins; parent IDs and both existing table roles preserved; no reuse of chart-bound inputs across
subjects."* Use the three representations: shared global astronomy (no per-chart copies of identical
sky data), chart-specific contacts as **lossless intervals**, dense samples only where an operator
needs them. The century materialiser's disposition is the family's central efficiency-vs-quality
call — Strategy §5: *"elevated complete materialization OR a qualified compact substrate with
explicit refinement semantics; deferral alone cannot earn elevation."* Coarse-to-fine is
acceptable only *"with an argument for candidate coverage and an explicit exact-refinement
contract"*; the Search-coverage object must accompany every no-window result.

## Synergy (lens 2.4)
**Owes:** Sangam a service contract (what the on-demand call returns, at what grain, with what
coverage); Kshetra the resonance targets without first-root loss (A05: *"deduplication must not
retain only the first root"*); Vighnakara/TRIGGER a single obstruction root that does not
attenuate twice (A08); the three served tools a generation they can select honestly. **Receives:**
resonance from L0–L2 rule capital; Moorti's *rolling −60/+400-day, day-grade Lahiri* coverage,
which must not be silently reused as century-complete (A06).

## Consumer walkthrough (lens 2.5)
Product §9 experience 4 and §7.1: *"compare closest eligible triggers and better-supported later
windows under explicit criteria, uncertainty and coverage; 'none found' includes the searched
horizon, resolution, qualified methods."* Walk `gochara_forecast_get` for the canonical chart and
for one **ordinary period**: what reaches synthesis today (DATE-grain windows, no contact), what
would reach it after elevation, and what the person can newly distinguish.

## Fences you cannot cross
Register fences 1–3 (generation-keyed mutation only; sweep v1 never touched; shared build state);
migration 566's BUILD-PROTECTED guard on century — working, not yours to weaken; the retired
sweep is a tombstone (register "Protected-retired exclusion"); no `kala_views/` edits — serving
changes are an L3-U11 interface packet with a sentinel test you own.

## Decisions to put to the native
Which member owns the served product and what `authoritative_generation` means post-elevation ·
century: complete materialization vs qualified compact substrate · whether the Contact object is
persisted (a new partition on an existing owner, per VA §10.3 "no new writer assumed") or served
on demand from the service · Kota/Tithi: proposed-use or retire the declared edge · what releases
the registry hold.

## Deliver
`GOCHARA_FAMILY_ELEVATION_BRIEF_v1_0.md` in contract §1–§8 shape with a **group section** (member
packets, shared-fence plan, one writer/one publication owner per packet, the served-product
owner), the latent-value register, the P3 equivalence contract, and the six A–J lenses per member
or `not_applicable` with reason. Supersede v0.3's recommendations only where evidence requires,
and say so. Propose; the native rules.
