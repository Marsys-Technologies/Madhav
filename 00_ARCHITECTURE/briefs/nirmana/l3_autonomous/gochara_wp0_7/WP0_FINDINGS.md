# WP0 — Findings re-validation record (2026-09-23)

Run: `l3/gochara-autonomous-wp0-7` @ `fd13ec0a6` (pin `c58e86662` is an ancestor; the
three commits beyond it are docs-only — source files identical, citations remain valid).

## N-0. Nutation-gap sign — PINNED by direct computation

Resolved by direct Swiss computation (pyswisseph 2.10.03, `SIDM_LAHIRI`), quantity
**δ = lon(FLG_SIDEREAL) − lon(tropical − get_ayanamsa_ut)**, Moon, noon UT:

| Date (noon UT) | δ (this computation) | brief v1.2 / E-OUTPUT | Astra F4 |
|---|---|---|---|
| 2020-01-01 | **+16.516356″** | +16.516″ | −16.518″ |
| 2026-01-01 | **−5.523005″** | −5.523″ | +5.522″ |
| 1984-02-05 | **+14.850808″** | +14.82″ (App. C, birth-instant jd) | −14.851″ |

**Verdict: the brief v1.2 / evidence-output signs are correct; Astra F4's signs are
inverted.** Mechanism (verified in the same run): δ equals the nutation in ecliptic
longitude Δψ of date to 0.001″ over a 2000–2040 scan (Mars and Moon), and a 1900–2150
scan bounds |δ| ≤ 18.9″. Equivalently: `FLG_SIDEREAL` applies the *apparent* ayanāṃśa
(Lahiri mean + nutation term), while `tropical − get_ayanamsa_ut` subtracts the *mean*
ayanāṃśa from an apparent tropical longitude. The registered finding now reads:
**"the two in-repo sidereal methods differ by the nutation in longitude of date:
+16.516″ on 2020-01-01, −5.523″ on 2026-01-01 (Moon, noon UT) — magnitude ≤ ~17″;
D-1 pins `FLG_SIDEREAL` (apparent), removing the gap."**

Registered as one signed figure pair, not two: **(+16.516″ / −5.523″)**.

## F-01..F-32 citation re-verification

Verification basis: `git diff --name-only c58e86662e..HEAD` over `platform/`,
`platform-mcp/`, `pipeline/`, `supabase/` — 68 files changed, **all docs/evidence; no
cited source file touched**. The pin's own accuracy was then checked citation by citation.

**Result: 33 citation groups CONFIRMED · 2 DRIFTED (±line shifts, substance unchanged) ·
0 GONE.**

| Cited | Status | Corrected location |
|---|---|---|
| `brahmagyan/l0_ephemeris.py:290` (G-6: TRUE calc under "mean" comment) | drifted −1 | "mean" comment at **:287**; `calc_ut(jd, 11, …)` at **:289**. Substance unchanged |
| `clear/route.ts:95-96` (stale migration-540 comment, §9 step 0) | drifted +24 | stale comment at **:119–120** |

Path clarifications (content confirmed; actual path differs from what a reader might infer):
`primitives.py` → `services/gochara_grammar/primitives.py` · `ka_sangam.py` →
`pipeline/orchestrator/writers/ka_sangam.py` · `bg_sky_calendar.py` and `bg_cohort.py` →
`pipeline/orchestrator/writers/` · `register_gochara_windows.ts` → repo-root `platform-mcp/`
· `AtlasView.tsx` → `platform/src/components/build/` · migrations split:
`platform/migrations/` holds 266, 460, 563, 568, 588, 670, 1018; `platform/supabase/migrations/`
holds 527, 540, 542, 556, 564, 566. No repo-root `Dockerfile`; the ephemeris-download cite
is `platform/python-sidecar/Dockerfile:24` + `Dockerfile.pipeline:17,22` (checksum
`ca1393ce…` confirmed matching §4.1's convention vector).

Notable confirmations load-bearing for later WPs: engine.py `:107` w30 enabled, `:632` the
executing λ product, `:668/:778` w30 stored, `:1063-1137` sentences computed-and-discarded;
primitives.py `:189-196` dṛṣṭi table with the refuted BPHS-Ch.26 node citation at `:193-194`;
`:664-719` the equal-eighths kakṣyā fixture on the served path; resonance `writer.py`
`:380-385` sensitive fetch with no value filter (F-19 mechanism confirmed);
`:518-549` the 27-class completeness gate.

## Consumer re-enumeration (F-25 lesson)

Fresh full-tree grep of `platform/python-sidecar/`, `platform-mcp/`, `platform/src/` for
`find_aspects`, `find_eclipse_proximity`, `search_long_horizon`, `kala_gochara_windows(+_v2)`,
`kala_gochara_authority`, `gochara_resonance_map`, `GocharaTransitService`, and the three NEW
relations. Basis: `grep -RIn` case-sensitive, all file types; SQL migrations checked separately.

**F-25's correction holds — no third undercount.** `find_aspects`: definition at
`services/ka_gochara/service.py:63`; callers exactly `kala_trigger/trigger.py:96,150,199`
(duck-type contract :87), `ka_sangam/engine.py:464`, `scripts/kala_admission/currents.py:59`
(docstring), plus test fakes. `search_long_horizon`: definition `transit_search.py:898`;
callers `ka_sangam/engine.py:1383` (bypass) and the service itself (:157). No hits of any
audited token in `platform-mcp/src` or `platform/src` for the Python class (TS reaches the
data via tables/tools).

**New relations `kala_gochara_contacts` / `kala_gochara_coverage` / `kala_gochara_publication`:
0 hits** — clean slate, confirmed.

**Callers the plan §6.1 does not name (recorded; escalated as E-004; NOT fixed here):**
1. `platform/src/app/api/mcp/db/query/route.ts:64,71,84` — the read-only proxy **whitelist**
   the MCP tools' SQL transits. A `'4.0'` publication touches it via whitelist entries, not
   only `register_gochara_windows.ts`. Load-bearing for P-1.
2. `scripts/kala_admission/w45_post_fit_rebuild.py:262` and
   `restamp_dishonest_staging_calibration.py:61,94,128` — SQL UPDATE writers on
   `kala_gochara_windows_v2` (calibration stamping; admin scripts).
3. `scripts/kala_admission/w41_lambda_contenders.py` (reads v1 + `_v2` λ),
   `w44_weight_fitting.py` (reads `_v2`), `w43_ablation_runner.py` (config refs).
4. `scripts/mr20_no_loss_coverage_gate.py`, `mr23_w12_adverse_golden_comparison.py`,
   `mr47_shape_conformance_gate.py` — gates reading v1/`'3.0'`/`_v2` corpora.
5. `services/w2g_validations/v5_corpus_readiness.py:42,44`, `v6_divergence_pilot.py:52` —
   read-only validation suite over windows + resonance_map.
6. `services/gochara_grammar/resonance_map.py:34,50` (read-side SQL accessor) and the
   `gochara_intensity/{engine,promise,enrichment,configuration_activity}.py` live-fetch
   readers of `gochara_resonance_map` — the internal mesh, unnamed in §6.1.
7. `services/ka_gochara_sweep/writer.py:259,337,554` — the still-registered v1 writer
   (INSERT/DELETE `kala_gochara_windows`; the F-03 Clear hazard's source).
8. `platform/src/lib/lel/prospective_ledger.ts:164,170,208,252,498` — docstring-level row-shape
   coupling (G-4 claim signatures) citing the windows/authority mechanism as its template.
9. `platform/src/lib/pariprashna/confidence/engine_tier.ts:6,7,11,13,67` — comment-level
   coupling to the authority-flip mechanism.
10. Registry-seed text surfaces (`platform-mcp/.../vidhi/registry_data.ts:780,794,808`,
    `platform/src/lib/vidhi/registry_data.ts`, `bg_vidhi_primitives.py:77,80,81`) — prose
    claims ("rows ACTIVE on the current date") a `'4.0'` cutover invalidates; seed file itself
    is HELD (must_not_touch) — packet N-9(ii) co-ownership concern.

**Plan §6.1 entries not grep-confirmable (recorded, not treated as drift):** the L5 `mi_*`
ledger references none of the audited tokens (its P-3 need for `contact_id` stands as a
design requirement, not a live reader); Saṅgam's `engine.py` has zero table-level hits (the
direct Vedha read is `pipeline/orchestrator/writers/ka_sangam.py:1037-1060` against
`kala_vedha_gochara`, a different table); D8 `register_d8_assess_domain.ts` has zero direct
hits (couples only via `fetchGocharaSweep`); cockpit stats routes carry no literal table
tokens (they read `count_sql` from the registry — consistent with F-24).

**Reader inventory for WP7 = plan §6.1 + items 1–10 above.**

## Historical ≥2-era case

No claim is made beyond: **misattributed diagnosis, unreconstructed.** (Exit-gate item.)
