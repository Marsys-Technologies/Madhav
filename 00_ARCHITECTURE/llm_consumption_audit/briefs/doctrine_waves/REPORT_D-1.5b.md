---
artifact: REPORT_D-1.5b
type: WAVE EXIT REPORT (CONDUCTOR_PROTOCOL §7 / §8.8.iii)
status: closed
---

# D-1.5b — Foundation Capabilities — CLOSE REPORT

## Status: CLOSED (Gate B = 17/17 GREEN on the deployed connector)

## Summary

D-1.5b delivered its 7-lane brief (chalit + real cusps, bhāva-bala + astakavarga,
Sudarśana Chakra, Bhavat Bhavam, small L1 completions, serving hygiene, governance +
derived view) and passed Gate B **17/17 green** on the deployed connector after a full
L1→L5 rebuild of Abhisek's chart (`482012f1`).

Getting there required, beyond the 7 lanes, discovering and fixing **three real
production defects during the mandated rebuild** and **four serving-layer gaps the live
Gate B battery surfaced** — each only visible after the previous fix deployed. Every
substantive fix was independently verified (fresh-context adversarial verifier, diff
review + live/DB reproduction, not self-certified) before merge.

## Lanes (7-lane brief, staged in 2 cycles)

**Cycle 1** — fact writers + astronomical core (merge order B-5 → B-1 → B-2):

| Lane | Verdict | Receipt |
|---|---|---|
| B-5 (small L1 completions: karakāmśa, shadbala ratio, D2 hora-class, ph_nimitta dedup) | RECEIPTED ACCEPT | verifier aeb81d309df523957 |
| B-1 (bhāva-chalit + real Sripati/Placidus cusps; quarantine fake KP cusps) · **headline, 2 verifiers** | RECEIPTED ACCEPT ×2 | compute-verifier aff6be16 (independent cusp recompute) + quarantine-verifier a1f5158b |
| B-2 (bhāva-bala via PyJHora 3-source; astakavarga sign-rekey) | RECEIPTED ACCEPT | verifier afe548aa |

Cycle-1 integration surfaced a cross-lane gap (B-1's 3 new `chart_facts` categories
undeclared in `CHART_FACTS_SCHEMA.json` → would fail the `drift_detector` gate; not
caught by pytest). Re-opened B-1 (targeted, commit 9f59a193 + a `TestSchemaDeclaration`
regression guard). Merged PR #570 → `417dadab`, deployed.

**Cycle 2** — consumers/serving/governance (B-3 → B-4 → B-6 → B-7):

| Lane | Verdict | Receipt |
|---|---|---|
| B-3 (Sudarśana Chakra tri-frame; `sudarshana_agreement` MSR class) | RECEIPTED ACCEPT | verifier a1dc2e1e (type specimen reproduced live) |
| B-4 (Bhavat Bhavam gated amplifier; 12-cell odd-house map) | RECEIPTED ACCEPT | verifier ab3ef46c (restraint guards hand-tested) |
| B-6 (serving hygiene: positions ordering, response budgets, CR-42, B9 dosha gate, kāla-sarpa facet) | RECEIPTED ACCEPT | verifier a793bc3c (baseline-diff confirmed) |
| B-7 (§N.6 density text + CI census harness + `dasha_lord_capability` derived view) | RECEIPTED ACCEPT | verifier aa528c12 (density harness run live) |

DR-3 (DIS.016) formalized the B-3/B-4 salience constants before spawn
(`sudarshana_agreement=1.15`, `bhavat_bhavam_amplifier=0.85`, subsystem=structural).
Cycle-2 integration: one expected `l0_class_priors.py` conflict (both B-3/B-4 appended
per the brief's coordination note), resolved keeping both. CI caught a real TAP-6/M-22
violation (B-3 hardcoded `two_pass_verified` literal → fixed to `documented_approximation`).
Merged PR #571 → `92a7df4c`, deployed.

## Defects found during the mandated full L1→L5 rebuild

| # | Defect | Fix | Verdict |
|---|---|---|---|
| 1 | B-4 `bhavat_bhavam_amplifier` — `to_msr_row` hardcoded `constituent_facts_array=None` (NOT NULL violation → 100% insert failure) AND an unbounded N×M candidate cross-join (>22,000 near-dup rows for one house-pair). Invisible to B-4's small-scale Phase-1 verification. | commit 89fe8824 — bounded to 1 signal per (primary,derived) house-pair (12/ayanamsha); real L1/L2 lineage threaded through | RECEIPTED ACCEPT (adversarial, incl. H1 self-corroboration edge + live specimens) |
| 2 | Same-class NOT-NULL-via-falsy-`or` bug in `_load_vichara_divergence_signals` (flagged by the #1 verifier) | commit 0e302504 (proactive) | folded into #1's review |
| 3 | `bo_laksana`'s `replace_prior_msr_for_chart` did an unconditional per-(chart,ayanamsha) `bodha_msr_signals` wipe — silently destroying B-3's `bo_sudarshana` rows on every rebuild (45 rows → 0 while asset_throughput lied `state=lit`). Surfaced when sudarshana served 0 post-rebuild. | commit 75e492e3 — scoped delete to a required `owned_signal_type_classes` allowlist; raises rather than blanket-delete | RECEIPTED ACCEPT (allowlist completeness + SQL placeholder hand-count + real-row-semantics regression test) |

Rebuild executed via the Cloud Run job path (`brahma-build-pipeline-job`) — the laptop
cloud-sql-proxy proved unreliable for `bo_samskara`'s long embedding loop (documented in
STATE_D-1.5b). L1 (22 `ga_*`) rebuilt once, cleanly; only L2–L5 re-run after the fixes
(user-directed, correctly avoiding a redundant L1 rebuild). Final estate: 65/65 assets lit.

## Gate B serving-layer gaps (surfaced by the live battery, fixed to green)

| Assertion | Gap | Fix (PR) |
|---|---|---|
| B_shadbala_ratio | `chart_facts_query`'s `WHERE ayanamsha_id=$2` hid ALL `ayanamsha_id='INVARIANT'` facts (`required_rupa` is INVARIANT) | `IN ($2,'INVARIANT')` — also un-hid naisargika + panchanga anchors (#575) |
| B2_sudarshana | `bodha_signals_get` never declared `signal_type_class` in its schema → the (pre-LIMIT) class filter was unreachable | expose the param; class-scoped query reaches the whole class regardless of global salience rank (#575) |
| B7_budgets | `bodha_domain_reading_get` 909KB → 155KB → 41KB. Two unbounded sections: each lens's `ranked_signals` (fixed pass 1) and `template_element_ids_jsonb.signal_ids` (fixed pass 2, exposed after pass 1) | cap both to per-lens budget with §N.6 disclosure (#575, #576) |
| B_d2_hora_class | D2 `varga_hora_class` rows live in `chart_divisionals` (the S-12 "MCP-invisible" EAV layer); no exposed tool surfaced them | `ganita_chart_facts_get(divisional_chart=…)` now serves them in a budget-capped, source-tagged `divisional_facts` section (#575) |

Two Gate B assertions (B2, B_d2_hora) also needed the *harness* updated to exercise the
new serving paths (they were testing the pre-fix way) — done in #576. Five other harness
bugs (wrong category/tool names + a density-floor pagination-truncation bug) were fixed
in 0566e1d6. The 4-fix bundle (#575) was adversarially verified including a DB-level
INVARIANT-pivot-collision analysis (no data corruption: the per-ayanamsha row wins the
one shared-key-name pivot slot; the other shared key is ayanamsha-invariant anyway).

## Gate B result

**17/17 green** on the deployed connector (amjis-mcp @ `470f2290` proxying amjis-web's
capability API). `bodha_domain_reading_get` confirmed 41KB (from 909KB).

**Rate-limit note:** the deployed connector rate-limits under the full 32-assertion
sustained load (429 cascade → false reds on unrelated assertions; the client only retries
5xx). The 17 D-1.5b B-* assertions run cleanly in one batch under that threshold; the
D-1.5a set passes in its own batch. Worth hardening the harness client (throttle/backoff +
retry on 2xx-with-error-body) in a future pass — flagged, not fixed.

## Carried-forward PARKs (out of D-1.5b scope)

The 2 non-B reds in the full battery (assertion 4 = CR-90 `keyword_heuristic_v1` valence;
A7 = `ganita_structural_get(facet=aspects)` parashari-aspects serving) are the **identical
2 items D-1.5a documented as PARKED** (REPORT_D-1.5a.md lines 75-76). Pre-existing,
non-regressions, outside D-1.5b's 7 lanes, and provably unaffected by D-1.5b's TS-serving-only
fixes (`valence_source` is a build-time field). They remain open agenda for a future wave.

## Non-blocking follow-ups flagged for the record

- Harness client rate-limit hardening (throttle/backoff + non-5xx error-body retry).
- `bodha_writers/__tests__/*` is not collected by the CI pytest target (pre-existing gap,
  shared with `test_formulas.py`) — B-4's restraint-rule tests pass directly but aren't in
  the standing gate. Recommend moving under `tests/` or extending the pytest target.
- `bodha_signals_get` alias passes `min_weight` but `query_signals` reads `min_salience`
  (silently dropped) — incidental, noted by the B2 fix agent.
- deploy.yml path-detection did not rebuild amjis-mcp for a `platform/`-only change; it was
  harmless here (amjis-mcp proxies amjis-web's capability API, which WAS rebuilt), but worth
  confirming the intended behavior.

## PRs

#570 (cycle-1) → `417dadab` · #571 (cycle-2) → `92a7df4c` · #572 (docs) · #573 (B-4
amplifier + Gate B harness) → `0682e023` · #574 (bo_laksana delete-scope) → `53d03d73` ·
#575 (4 serving-gap fixes) → `1a4b935f` · #576 (B7 2nd-pass + assertion wiring) → `470f2290`.
All CI-green, deployed, live-SHA verified.
