# FOCUSED ELEVATION DISCUSSION — the Gochara family

You are opening a **dedicated design discussion** with the native (Abhisek Mohanty) about the
Gochara assets in L3 Kāla. **This is a discussion, not an execution session.** Do not write
production code, do not dispatch builds, do not open PRs. Your deliverable is one reviewed brief.

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

- `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` — §5 (efficient
  computation), §6.1 rows L3-A05/A13/A14/H01, §6.3 (computational vs declared edges)
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/MADHAV_L3_ASSET_ELEVATION_PLAN_v1_0.md` — §1 (the
  ten dimensions of elevation), §2 Tier S, §5 Q1
- Root `CLAUDE.md` §N.4–§N.8
- Code: `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara.py`,
  `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py`, `platform/python-sidecar/services/gochara_v3/**` (8,441 LOC),
  `platform/python-sidecar/services/w2g/**`, `platform/python-sidecar/services/gochara_grammar/**`, `platform/python-sidecar/services/gochara_intensity/**`,
  `platform/python-sidecar/services/ka_gochara_resonance/**`, `platform/python-sidecar/pipeline/transit_search.py`

## The measured situation — verify each before relying on it

Four assets carry the `ka_gochara*` prefix, and **their table ownership is contradictory across
sources**:

| Asset | `target_table` per the seed | Status |
|---|---|---|
| `ka_gochara` | `kala_gochara_windows` | active, T1, ±3-year bounded search |
| `ka_gochara_sweep` | `kala_gochara_windows` | **RETIRED — shares the table with the active asset** |
| `ka_gochara_v3_century_materialize` | `kala_gochara_windows_v2` | active, **ON HOLD**, century scope |
| `ka_gochara_resonance` | `gochara_resonance_map` | active, T0, feeds all three |

**The approved strategy document disagrees with the seed.** Strategy §6.1 L3-A13 states
`ka_gochara` produces `kala_gochara_windows_v2` "generation 2.0" — but the seed assigns that table
to the century materialiser. Establish which is true in the live database and in the frozen
campaign manifest before anything else. Do not assume either source is correct.

Three further measured facts:

1. **Retired history shares a live table.** `ka_gochara_sweep` is protected, non-rebuildable
   history writing the same `kala_gochara_windows` an active asset writes. Any delete-then-insert
   rebuild of `ka_gochara` is a hazard to protected history (§N.3, strategy §9.4).
2. **The century materialiser declares inputs its code does not consume** — `ka_kota_chakra`,
   `ka_tithi_pravesha` and (per strategy) `ka_sudarshana_varsha` are declared `depends_on` edges
   with no corresponding read. Those same three assets are consumed by nothing else either.
3. **`platform/python-sidecar/pipeline/transit_search.py` is a cross-stream hub** — imported by Kshetra, Sangam, this family, and
   L0's already-frozen `bg_sky_calendar`. Editing it invalidates accepted analyses elsewhere.
   Strategy items P3/P4 want to change exactly this file.

## What the discussion must settle

Put these to the native. Explore, argue both sides, then record the ruling — do not decide alone
and do not let a default emerge by silence.

1. **Is `ka_gochara` superseded by the century materialiser, or are they complementary?** The
   native's working understanding is that one supersedes the other. Test that against the code.
   If it is supersession, the superseded asset needs an evidenced retirement disposition, not a
   silent elevation. If complementary, each needs a distinct qualified purpose.
2. **Q1 from the elevation plan — full century materialisation, or a qualified compact substrate
   with explicit refinement semantics?** A hold cannot close by deferral. ~11k LOC of work turns
   on this. Bring cost, coverage and a concrete failure mode for each option.
3. **What is the honest coverage contract?** `ka_gochara`'s ±3-year progressive search and the
   century's era/resolution grid are different claims. A caller must be able to tell "no window in
   the searched range" from "outside the searched range" from "search incomplete".
4. **How is protected sweep history isolated** from an active rebuild sharing its table?
5. **What is the actual read DAG**, as opposed to the declared one? Sangam reads live transit
   geometry rather than the materialised table; the registry says otherwise. Record every
   discrepancy with its type: computation, scheduling, validation, serving, or unresolved dynamic.
6. **Do the three declared-but-unconsumed inputs earn integration, or retirement?** (Elevation plan
   Q2.) This overlaps a portfolio decision; surface it rather than resolving it unilaterally here.

## Deliverable

`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/BRIEF_GOCHARA_FAMILY_v1_0.md`, containing:

- The **verified** asset/table/ownership map, with the seed-vs-strategy contradiction resolved
  against live evidence and the frozen manifest, and the method you used to resolve it
- Per asset: qualified purpose, coverage contract, field/producer obligations (elevation plan D1),
  and the structure that must survive (D2, D3)
- The native's ruling on each numbered question above, with rationale — including any left open
- The retirement/supersession disposition for whichever asset does not survive as active
- The exact read DAG vs declared DAG, discrepancies typed
- A `platform/python-sidecar/pipeline/transit_search.py` change protocol, since P3/P4 collide with a frozen L0 closure
- What is **not** settled, named plainly

## Conduct

Ground every claim in file, line or live query. Where the strategy and the code disagree, say so
rather than smoothing it. An honest "this is unresolved and here is what would resolve it" is
worth more than a confident map that is wrong. Do not invent astrological doctrine; where method
qualification is missing, that is a real requirement to route to its authority.
