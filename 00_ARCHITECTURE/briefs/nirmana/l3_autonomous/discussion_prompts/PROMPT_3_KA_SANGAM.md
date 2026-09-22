# FOCUSED ELEVATION DISCUSSION — ka_sangam

You are opening a **dedicated design discussion** with the native (Abhisek Mohanty) about
`ka_sangam`, the convergence asset and the structural chokepoint of L3 Kāla. **This is a
discussion, not an execution session.** Do not write production code, do not dispatch builds.
Your deliverable is one reviewed brief.

## Where you are (added 2026-09-22 — this was missing and is why the prompt failed)

All paths below are **relative to the repository root**. Anchor yourself before reading anything:
the Python for this layer lives under `platform/python-sidecar/`, NOT at the repo root — a path
like `pipeline/transit_search.py` does not exist as written; it is
`platform/python-sidecar/pipeline/transit_search.py`. Every code path in this prompt has been
corrected and verified to resolve. Governance artifacts under `00_ARCHITECTURE/` are already
repo-root-relative.

**Read this too, before the list below:**
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md` — the context that
changed since this prompt was written (no invented confidence scalar; bind to F04/F06/F12 + the
Strategy §3 Temporal-Testimony object; L3-Q01–Q13 as the ratified baseline; generations as the
probable substrate; "disposable data" scoped to rebuildable projections only; serving is a Pūrṇa
interface packet). It supersedes anything below that conflicts with it.

## Read first

- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` — §2 (L3-Q02, Q05),
  §3 ("Temporal testimony" and "Engagement route" objects), §5 P4, §6.1 row L3-A15, §6.3,
  and the **L3-U02** row in the cross-layer table
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` — §1, §2
  Tier S, §5 Q3 and Q8
- Root `CLAUDE.md` §N.5 (L1 is authority over L2+ derivations), §N.6, §N.7
- Code: `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` (1,166 LOC),
  `platform/python-sidecar/services/ka_sangam/engine.py` (1,812 LOC), `platform/python-sidecar/services/kala_trigger/**`,
  `platform/python-sidecar/pipeline/transit_search.py`

## Why this asset is different

**Sangam is the chokepoint. Seven of the twenty-one depend on it** — `kalasutra`, `vighnakara`,
`taranga`, `kala_darshana`, `tulana`, `bhavishya_lekha`, `jivana_parva`. Nothing in tiers T3–T5
can be elevated until Sangam's semantics are right. Getting this wrong propagates to a third of
the layer; getting it right unblocks the whole spine.

## The measured situation — verify before relying on it

**Caps found in code** (`platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py`):
- `ORDER BY dignity_score DESC NULLS LAST, p.id ASC LIMIT 200` (~line 247)
- a "near `LIMIT 200` / lifetime `LIMIT 60`" framing (~line 386)
- `platform/python-sidecar/services/ka_sangam/engine.py:1102` — `list(dasha_rule.get('constituent_lords', []) or [])[:1]`, i.e. **only the
  first constituent lord is retained**
- `platform/python-sidecar/services/ka_sangam/engine.py:1124` — `max_level=3`

**Declared vs actual reads.** The registry declares 10 dependencies including a materialised
`ka_gochara` edge. The strategy states Sangam actually reads **Vedha and on-demand transit
geometry**, not the materialised table. Treat both as claims to verify.

**Identity gaps.** Strategy §6.1 records that Sangam's output carries "one domain and missing
ayanamsha identity" needing review.

**Independence.** Sangam currently presents convergence constituents as independent witnesses.
Strategy L3-U02 is explicit: declared lineage groups are bookkeeping, **not demonstrated
statistical independence**; zero supporting evidence cannot become one independent witness, and
another representation of the same origin adds no independent support.

## What the discussion must settle

1. **Q3 from the elevation plan — what counts as an independent witness?** This is epistemics,
   not code, and it determines whether a convergence score means anything at all. Shared natal
   roots, the same rule reached by two paths, and two genuinely disjoint methods must be
   distinguishable in the output. Agree the definition before anything is built on it.
2. **Q8 — the truncation policy, decided here first because Sangam is where it bites hardest.**
   `LIMIT 200`, `LIMIT 60`, `[:1]` on constituent lords, `max_level=3`. For each: is it a genuine
   semantic bound, a performance cap, or an accident? A cap a caller cannot distinguish from a
   true absence destroys the coverage contract. What replaces each one?
3. **What is a convergence, in the native's own terms?** Simultaneous interval intersection with
   parent hierarchy and applicability — not equality of arbitrary date pairs, and not a union of
   systems from disjoint windows. Get the native's definition explicitly; the implementation
   should be judged against it rather than the reverse.
4. **The `[:1]` constituent-lord truncation** looks like the "retain only the first root" defect
   class the strategy names for Resonance. Confirm whether Sangam's scoring is currently built on
   a single lord where the rule has several — and what the correct representation is.
5. **Modes.** Which Sangam modes are qualified and which are legacy? Each surviving mode needs a
   distinct qualified meaning, not a name.
6. **Ayanamsha and domain identity.** Should ayanamsha be part of the natural key? What is the
   correct multi-domain representation, given the strategy forbids one-domain flattening?
7. **P4 shared geometry** — geometric search results may be reused across compatible
   predicates/modes only if each rule's, parent's and method's testimony survives. Note the
   constraint: this touches `platform/python-sidecar/pipeline/transit_search.py`, which sits inside already-frozen L0
   (`bg_sky_calendar`) and is imported by Kshetra and the Gochara family. Any change is a
   coordinated cross-stream invalidation, not an in-stream edit.
8. **L1 authority (§N.5).** Sangam must reference L1 `fact_id`s and inherit their values, never
   restate a computed value as its own. A disagreement between a Sangam derivation and the L1
   fact it cites is halt-worthy, not a stored divergence. Confirm the current code obeys this.

## Deliverable

`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/BRIEF_KA_SANGAM_v1_0.md`, containing:

- The native's definition of convergence and of an independent witness, stated precisely enough
  to test an implementation against
- A per-cap disposition table: cap, current value, classification, replacement, how a caller
  learns the bound
- Verified actual-read DAG vs declared, discrepancies typed
- Field/producer obligations for `kala_convergence` (elevation plan D1) and the structure that
  must survive (D2, D3) — participants, roles, signed relations, evidence roots, independence
  group, applicability, material uncertainty
- Mode dispositions
- The ayanamsha/domain identity decision
- A P4 shared-geometry position including the `platform/python-sidecar/pipeline/transit_search.py` change protocol
- What is **not** settled

## Conduct

Ground every claim in file, line or live query. Because seven assets inherit this asset's
semantics, prefer an honest open question over a provisional answer that will propagate. Do not
invent doctrine on independence or convergence — elicit it, and where the native's answer implies
a method not currently admitted, record that as a requirement for its authority rather than
assuming it.
