---
artifact: NEAR_MISS_DOMAIN_PACKET
version: 1.2
status: DOMAIN_REVIEWED_APPROVED_WITH_NARROWING
date: 2026-09-29
ruling: OSR-015 (conductor execution of the packet's own pre-authorized fallback; no new decision)
amends: NEAR_MISS_DOMAIN_PACKET_v1_0.md and _v1_1.md
changelog:
  - 1.2 (2026-09-29): independent Parashari domain review (BPHS Ch.41 via the classical-text tools) found the dusthana placement gate that defines near_miss NOT FOUND as a formation condition in Ch.41 (only adjacent, conditional Ch.42 afflictions). Per packet v1.0 section 8 ("if the dusthana gate cannot be sourced, near_miss is removed from v1 ... nothing widens") near_miss is removed. Candidate set, tolerance none, D1 whole-sign frame and the present/absent/indeterminate states are unchanged.
---

# Near-miss packet v1.2 — narrowing after independent domain review

## Decision (mechanical application of v1.0 §8)
- `near_miss` is **not a v1 state**. The band serves `present`, `absent`, `indeterminate`; `near_miss_capable_candidates: 0`; `band_coverage.near_miss` is always 0. The route never emits `near_miss`; the dusthana-gate near-miss logic is not exposed.
- The consumer field `notably_absent_yogas` therefore serves an empty array by design, with `band_coverage` (present/absent/indeterminate counts), `near_miss_capable_candidates: 0` and an explicit note that formation-gap detection is not claimed. It never says `not_computed`.
- Any future near_miss requires a quotable BPHS verse for the gate and a new packet version plus domain review; it never widens by default.

## Required amendments from the domain review
1. **Re-cited pair rules.** BPHS Ch.41 directly supports only the 5th/9th lord pair (sloka 16). The 2nd/11th, lagna/2nd, 9th/11th and any-pair-among-2,5,9,11 candidates rest on general Parashari sambandha (conjunction, exchange, mutual aspect) and translator's notes (e.g. 2nd/11th at the Ch.11 note), not on Ch.41 text. The L0 citation "Ch.41 Dhana Yoga adhyaya" carries no verse; the band's `classical_sources` must say so and must not present a verse it does not have.
2. **Subsumption / non-independence.** `dhana_yoga_2_5_9_11` subsumes 2-11, 5-9 and 9-11; `dhana_yoga_house_lords` overlaps all of them. The six rows are candidate statuses, not six independent findings; consumers must not sum them into a "yoga count". The response states this and carries `contradicting_present_siblings` / `overlaps` per row.
3. **Gate scope ambiguity** ("the meeting house" vs "either lord in a dusthana") is recorded as an open question for any future gate proposal; it is not resolved by v1.2 because the gate is removed from v1.
4. **Nodes and aspects.** Lordship must use only the seven Parashari planets (verify `NB_SIGN_LORDS`); special aspects (Mars 4/8, Jupiter 5/9, Saturn 3/10) must be honoured by the mutual-aspect test (verify `_nb_aspects_house`). The implementation adds tests that pin both, or reports the discrepancy.

## Consumer honesty rules added by code review
- If any candidate is `indeterminate`, the unit is **not settled**: the checklist must not read `exhaustive: true` because near-miss is empty.
- `ayanamsha_sensitive: false` may be asserted only when every neighbouring ayanamsha was actually compared; otherwise `null`. Zero comparable neighbours gives `null` with a note, not `false`.
- Zero L1 firing rows for the served build makes the affected candidates `indeterminate` with reason `no_l1_firing_rows_seen`, not `absent`.

## Security conditions applied (security review)
- Bound the ayanamsha fan-out to the closed set of canonical ayanamshas (max 5) and cache route results per (chart, ayanamsha, sorted build ids) with a short TTL; `statement_timeout` on the route connection; test that `judgment_query` is a per-chart primitive that denies an unauthorized `chart_id`.
- Production sets `PYTHON_SIDECAR_API_KEY` on both web and sidecar from the same secret (verified read-only, names only); the global sidecar dependency is left unchanged and its fail-open behaviour for sibling routers is recorded as a residual for the sidecar owner.

## Stale descriptor text (follow-up, not changed here)
`register_d9_judgment.ts` descriptor still says near-miss "needs a data-plane addition ... not_computed ... cannot manufacture closure". Changing it moves the capability content hash pinned by goldens this session cannot edit (`platform/tests/pariprashna/route_ports/baseline/*.json`) and by the acceptance artifact; re-point it in the next hash-regeneration wave.
