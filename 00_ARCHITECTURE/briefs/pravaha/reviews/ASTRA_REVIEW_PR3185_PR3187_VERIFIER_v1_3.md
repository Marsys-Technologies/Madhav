VERDICT: REJECT — PR 3185; REJECT — PR 3187.

**Neither PR is mergeable at `6132d0e519`.** Two P2 blockers remain: the missing-`lel_id` fallback in PR 3185, and a newly reproduced junction-boundary regression in PR 3187. The other three round-3 blockers are resolved.

**203 checked-in pure tests pass.** I replayed the original probes, checked the amendments against `1ef6639bf`, and inspected the full eight-file change. No files changed; no database or network access used. The mutation harness was not run.

References: **MR** = [measuring_report.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR4x/platform/python-sidecar/services/gochara_kernel/measuring_report.py), **NM** = [near_miss_verifier.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR4x/platform/python-sidecar/services/gochara_kernel/near_miss_verifier.py), **ND** = [nd_h_tables.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR4x/platform/python-sidecar/services/gochara_kernel/nd_h_tables.py), **MH** = [mutation_check_verifier_side.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR4x/platform/scripts/gochara/mutation_check_verifier_side.py). Times below are UTC unless labelled.

**P2 — PR 3185: a candidate first event without `provenance.lel_id` is still accepted. Must block merge.**

**MR:169–177, 228–236.** `_lel_id` substitutes a dated top-level `event_id`; the missing-ID detector then checks that substituted value.

With an identifiable birth row, birth date `1984-02-05`, rebuild date `2026-10-05`, and this event:

```python
{
    "event_id": "EVT.1998.02.16.01",
    "event_date": date(1998, 2, 16),
    "date_confidence": "exact",
    "shape": "point",
    "provenance": {},
}
```

Actual result is **accepted**, with horizon `1998-01-01 .. 2084-02-05`, `excluded_undated=0`, and that event selected.

The binding ruling requires **`lel_id_missing_on_candidate_first_event`**. Replacing the top-level ID with a UUID correctly triggers that refusal, demonstrating that the fallback is the bypass.

`test_measuring_report.py:169–170` explicitly protects the forbidden fallback. Remove it from the implementation and reverse that assertion. The original provenance/conjunction cases otherwise now work.

**P2 — PR 3187: the junction amendment treats an approximate reconstructed boundary as exact. It newly accepts a false junction and refuses an honest one. Must block merge.**

**NM:449–451, 486–491.** Endpoint matching permits two seconds of disagreement, but junction membership uses the reconstructed endpoint without accounting for its uncertainty. `contact_reconstruct.py:29, 65–73` promises a boundary within one second and returns the upper bracket.

Concrete input:

```text
TC       = 2000-01-15T12:00:00Z
x        = elapsed days from TC
d(x)     = min(1.1, 0.75 + 0.25*x*x)
body     = Mars
centre   = 100°
orb      = 1°
horizon  = [TC − 3 days, TC + 3 days)
```

This curve respects Mars’s stated speed bound. Its analytical band boundaries are:

```text
t_in  = 2000-01-14T12:00:00Z
t_out = 2000-01-16T12:00:00Z
```

The reconstructed `t_out` is **`2000-01-16T12:00:00.659180Z`**.

Store the analytical interval, clearance `0.75`, proximity `0.25`, closest time `TC`, and provide an MD/AD boundary at **`2000-01-16T12:00:00.500000Z`**. That event is outside the true stretch: its separation is **`1.000002893527°`**, beyond the inclusive 1° band.

| Stored junction | Round 3 | Current HEAD |
|---|---|---|
| `[]` — correct | Accepted | **Wrongly refused** with `near_miss_junction_mismatch` |
| `["dasha_md_ad_boundary"]` — incorrect | Refused | **Falsely accepted**; both row and set checks return `[]` |

I loaded the round-3 source in memory to confirm this before/after result; no source files were rewritten.

The fix must retain independent geometry while respecting boundary uncertainty: refine membership sufficiently, or return a named unresolved result near an uncertain boundary. Reverting to stored-endpoint membership would restore the original defect.

**Disposition of the five round-3 blockers**

| # | Status | Original probe replay and evidence |
|---|---|---|
| 1. Wrong LEL ID field/conjunction | **Partly** | UUID `event_id` plus valid `provenance.lel_id` now gives `1998-01-01`. Exact-flagged `EVT.1995.XX.XX.01` is excluded and reported. A dated top-level ID cannot override undated provenance. Missing-provenance fallback remains the blocker above. **MR:169–245**. |
| 2. Jupiter/Saturn contribution | **Resolved** | Identical ten-day Jupiter/P3, Jupiter/P4, Saturn/P4 supports now give Jupiter **10 exclusive days against class admission**. The transposed Saturn case also gives 10. P4-only records report both agents, each contributing 10; Venus/P3 covered by P4 contributes zero. **MR:590–593, 643–653**. |
| 3. Digest trailing newline | **Resolved** | `"d"*64 + "\n"` now produces **`marker_digest_malformed`**, both directly and through the scripted reader. Valid lowercase hex passes; integrity remains null with its reason. **MR:319–320, 379–382**. |
| 4. Candidate interval accepts wrong closest time | **Resolved** | Original `min(1.1, .5 + sqrt(x*x+.000001) − .001)` probe at **11:54:50** now produces **`near_miss_t_closest_separation_mismatch`**. True noon and the independently estimated minimum pass. **NM:469–485**. |
| 5. Endpoint shift hides junction | **Partly** | Original quadratic probe, boundary at reconstructed `t_in`, stored start shifted one second, empty junction: now correctly refuses. The amendment introduces the independently demonstrated boundary-uncertainty defect above. **NM:486–491**. |

**ND-H and ND-P2**

I independently transcribed the ruling’s table and compared all **40 tier/kāraka cells**, plus frame and noted-house metadata. They match **ND:50–97**.

| Class | CORE | DVI | SUPPORT | K-A | K-B |
|---|---|---|---|---|---|
| achievement_recognition | 10 | 11 | 1, 5, 9 | Sun, Jupiter | — |
| business_launch | 7, 10 | — | 6 | Mercury | — |
| financial_deception | 2, 12 | 6 | 8 | Rahu | — |
| foreign_settlement | 12 | 4 | 7, 9; 10 noted | Rahu | — |
| parental_event, father | 9, 2 | — | 4, 8 | Sun | Sun |
| property_acquisition | 4 | 11 | 2 | Mars | — |
| psychological_arc | 4 | — | 5, 8 | — | Moon |
| spiritual_turn | 5, 9 | — | 12 | Jupiter, Ketu | — |

The father frame, unsupported mother, spiritual Saturn testimony, DVI’s P4-only placement and `1.2.0` stamp checks agree. The ERRATA’s withdrawn citations are not reinstated as authority.

ND-P2’s natal-Sun bereavement licence passed **216 independent agent/path/relation/band combinations**, including the exact 1° edge. MD/AD karakatva, PD testimony, and absence of a blanket fast/slow gate agree. A1–A3 remain literal and labelled open. DVI lord-point handling remains explicitly unmodelled; psychological-arc P2 exclusion remains labelled draft.

**Arithmetic and other adversarial checks**

- **P4 and contributions:** 1,000 independently calculated cases matched across the build and scored grids, including agent removal, overlapping records, absent agents, abutting intervals, K-B/DVI variants and horizon clipping. Abutting or same-day disjoint Jupiter/Saturn supports admit zero P4 days. **MR:473–531, 582–653**.
- **Scored convention:** the scorer itself uses IST dates, inclusive endpoints and **10,334 days**: `gochara_eval/registry.py:8–21`, `extract.py:65–67`, `metrics.py:80–87`. The original midnight probe gives **4,134/10,334 = 40.0038707%**, triggering the guard. A support crossing `18:30Z` counts two scored dates and one UTC build date. No mixed-convention ratio reproduced. **MR:454–462, 507–531, 665–690**. I found no `EVALUATION_PROTOCOL_v2_3` artifact under `00_ARCHITECTURE`.
- **Scored-role filter:** admitted testimony refuses in the pure report; SQL positively requires both admitted and scored. **MR:606–607, 719–724**.
- **Horizon fallback/birth vocabulary:** zero rows use the rebuild date; a nonempty undated log refuses by name. Subcategory, provenance-subcategory, `domain="other/birth"` and `event_type="birth"` work. **MR:131–138, 263–280**.
- **Near-miss geometry:** ordinary and hidden crossings become contacts; exact-band plateaus and both sides of the 0/360 wrap work; horizon-clipped rootless stretches remain unresolved. Original near-equal minima at `2000-01-15T00:00Z` and `2000-01-16T00:30Z` both pass; unrelated times refuse.
- **Binding and finite values:** row validation plus set comparison reject wrong clearance, proximity, ordinals, orb, identity and duplicates. Stored Decimal values pass. Non-finite stored geometry and position callbacks refuse by name. These checks require both validation surfaces; `compare_sets` alone does not check proximity.
- **Resolution limit:** the original 18.93-second excursion remains undetected, but the result explicitly carries the **60-second named limit**, `complete=False` and `verified_empty=False`. **NM:195–202, 248–250, 505–507**.

**Minimum certificate and cost**

The lower bound is sound for finite geometry satisfying the stated Lipschitz bound:

```text
lower = max(0, (|d0| + |d1| − L × gap) / 2)
```

Golden-section refinement supplies an upper estimate; branch-and-bound excludes materially lower values. The certificate therefore concerns the minimum **value**, not a unique time. The new stored-time separation check addresses that distinction correctly.

Termination is bounded by the one-second floor, 40,000 evaluations per certificate and 3,000,000 position evaluations per search. My synthetic measurements were:

| Input | Evaluations/calls | Result |
|---|---:|---|
| Flat 0.5°, Moon bound, one day | 24,958 | Certified |
| Same, three days or 31,446 days | 40,000 | Uncertified; budget exhausted |
| Moon at 13.176358°/day, 86 years, 1° band | 209,398 | 1,151 contacts; 0.45 s |
| Same, 3° band | 222,555 | 1,151 contacts; 0.46 s |
| Exact-band plateau, 86 years | 3,000,000 | Named budget refusal; 7.76 s |

These are synthetic callback timings. The 0.0005° certificate tolerance is explicitly tied to one tenth of the clearance floor; astronomical speed maxima and the storage-rounding allowance remain independently unqualified, as previously recorded.

**Independence, readers and test evidence**

Runtime kernel imports are unchanged: **MR and ND import none; NM imports only `contact_reconstruct` at line 220**, implementing the ONE-band ruling. That shared detector is a shared failure surface, including the boundary precision relevant to the new blocker.

Test kernel imports are MR, ND, NM/`utc`, and `contact_reconstruct` in `test_near_miss_verifier.py:334, 351, 392, 531`. They are appropriate as test subjects and consistency checks; equality with the shared detector is not independent geometric proof. DB tests import MR and A5.3 setup helpers at lines 15–19, appropriately for integration fixtures.

The reader SQL matches migrations **1081, 1153, 1155 and 1156** and consists of parameterized SELECTs. Unbounded support ranges refuse; empty supports remain empty; aware timestamps and Decimal comparisons pass. An absent near-miss table remains unknown, not zero.

For LEL, baseline **001:463–473**, expanded baseline **0001:2056–2070**, migration **423**, **457** and later references including **691** support the inspected fields. Standalone `subcategory` is not established as a database column. The module receives LEL rows rather than issuing its own LEL query. Intake stores the human ID in provenance at `lel_intake.py:1314–1317`.

The new contribution, digest and closest-time tests protect their corrected claims. Two important test defects remain:

- `test_measuring_report.py:170` asserts the forbidden fallback.
- `test_near_miss_verifier.py:651–660` places its junction at the detector’s own reconstructed boundary. It detects the original displacement bug but misses disagreement with an analytically known boundary.

The mutation specification contains **78 mutants and two declared equivalents**. Every replacement target occurs once and every replacement compiles in memory. Both equivalence explanations are justified. A zero-exit baseline is required. No mutation kill count was verified.

**Carried P3 hardening — follow-up only, not additional merge blockers**

These were not worsened by the amendments:

| Item | Concrete current result | Evidence |
|---|---|---|
| Finite helper inputs | Certified `clearance_deg=inf` classifies as near-miss; NaN speed can return an empty search; NaN K-B separation returns false. | **NM:76–84, 224–231; ND:153** |
| Marker shapes | `test_slice=True` raises `AttributeError`; `{"horizon":123}` raises `TypeError`. | **MR:413, 422–426** |
| Mutation classification | Explicit `failure type="TypeError"` with an `AssertionError` message is credited as CAUGHT; exit 3 with passing cases is SURVIVED. | **MH:130–146** |
| Candidate shape | Reversed candidate interval `[tc+2s, tc−2s]` still passes when slack bridges it. | **NM:479–481** |
| Stale claims | Removed scored-horizon constant/open-convention wording, unused closest-time tolerance, and obsolete nonempty-log fallback docstring remain. | **ND:239; NM:49; MR:252–253** |

I did **not** verify database execution or production rows, real ephemeris accuracy/runtime, astronomical speed maxima, builder-table equality, verification-job wiring, stationless-body enforcement, source/precision identity binding, full-domain provenance, complete-build census, or actual layer-on/off scored outputs and all five endpoints. Those remain job-acceptance obligations; they are not newly promoted merge blockers here.

