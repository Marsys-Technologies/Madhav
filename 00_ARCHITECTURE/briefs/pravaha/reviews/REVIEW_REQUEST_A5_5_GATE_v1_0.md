---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.0"
author: "Stream B (Śāstra) — Kimi Code"
date: "2026-10-01"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward, never by this stream"
authority: "Review request only; authorizes nothing. Reviews are the steward's to dispatch (PRAVAHA_EXECUTION_ARCHITECTURE §5.10)."
bundles:
  - "GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT (AM-1..AM-9), commit f870999c1, campaign/pravaha"
  - "PR #2817 (HOLD): migrations 1204/1205 + the flagged selector widening"
  - "ORACLE_EXECUTION_MAP v1.1, commit 7e02d24f1, campaign/pravaha"
---

# A5.5 gate review request — one packet, three exhibits

The A5.5 gate is the single Codex review that unfreezes the Gochara v1.5 contract
work. Three exhibits have accumulated since v1.4 was FROZEN; they interlock (the
amendment list says *what* the contract should say, #2817 is the *schema* that two
of the amendments need, the oracle map is the *test evidence* that the seam those
migrations serve is honestly covered). Judge them in one pass so the verdicts are
consistent. PR #2817 is on HOLD until this gate returns.

## Exhibit 1 — the v1.5 amendment list (AM-1..AM-9)

File: `00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md`
(commit `f870999c1`, branch `campaign/pravaha`). The batch checklist at its end
(:298-310) is the one-page summary. Per item:

- **AM-1..AM-5** — settled implementation pins (steward M20261001T015412-6df0).
  Fold verbatim? Each cites its evidence: AM-1 convention-row values
  (`gochara_kernel/knots.py:169`, `step06_candidate_build.py:73,77,84`,
  `1153_gochara_sky_event_substrate.sql:584-596,1243`); AM-2 sha256→UUIDv8
  identity (`GOCHARA_DESIGN_SPECS_v1_4.md:615-622`,
  `GOCHARA_TEST_ORACLES_v1_4.json:64`); AM-3 two-phase substep grain
  (`GOCHARA_DESIGN_SPECS_v1_4.md:802-805`); AM-4 Moon/day tier EPHEMERAL
  (`1153:684-685` vs `1153:1072-1073`); AM-5 coverage-partition ownership
  (`1155_gochara_relationship_record.sql:72-80`, `1156_gochara_eval_window.sql:14,63`).
- **AM-6 — the only open decision.** `sad_bala_summary` units: the factor
  declares `units="rupas"`, `range=[0,1]` (`services/gochara_rules/registry.py:453-455`,
  branch `pravaha/b5-rule-paths`); `rupas` is not in `kgf_units_ck`
  (`platform/migrations/1154_gochara_rule_path_registry.sql:331`) and `[0,1]`
  contradicts the cited pūrṇa-bala thresholds (5–7 rūpas, Phaladīpikā IV.22–24,
  PG79:C1/PG80:C1, per `design/PROMISE_NATURE_YOGA_MAP_v1_1.md:37`). **Pick A
  (extend the enum, protected window), B (unitless ratio vs the cited threshold),
  or C (split: binary cited predicate + raw magnitude as unscored payload).** The
  draft deliberately makes no pick; its doctrinal note (:204-206) is that only the
  threshold *predicate* is cited, so any encoding keeping that binary and labelling
  the finer gradations uncited is safe.
- **AM-7** — `object_role='av_qualifier'` (accepted by the steward
  M20261001T121451-1a8d; implemented as migration 1204 in Exhibit 2).
- **AM-8** — P6 frame-kind `'inherited'` (migration 1205, Exhibit 2; binds with
  the `day_on_demand` step — the gate may sequence it after P1–P5).
- **AM-9** — FINDING for the L0 owner, not a spec change: Phaladīpikā XXVI.2
  (PG321:C1, "Rāhu and Ketu are similar to the Sun") gives both nodes {3,6,10,11}
  from janma-rāśi; the L0 seed carries Rāhu {3,6,11} (10 omitted,
  `l0_transit.py:758-784`) and Ketu {3,6,11}+12 (`l0_transit.py:841-875`, the 12th
  cited `BPHS_CH29` — a node-over-Moon affliction citation, not a favourable 12th).
  Disposition asked of the L0 owner: repair the 10s, justify or drop Ketu-12,
  upgrade citations from `RAHU_KETU_HOUSE_VEDHA_UNSOURCED` to PG321:C1. **No spec
  or registry change requested** — confirm that disposition is correctly scoped.

**What to judge (Exhibit 1):** Are AM-1..AM-5 faithful to their pins and evidence?
Is the AM-6 analysis complete (any fourth option missed?) and which of A/B/C
should the gate take? Is AM-9 correctly routed to the L0 owner with no v1.5
footprint?

## Exhibit 2 — PR #2817: migrations 1204/1205 (+ the flagged selector widening)

PR #2817 (branch `pravaha/b6-v15-contract-migrations`, **HOLD — this gate**).
Files:

- `platform/migrations/1204_gochara_av_qualifier_object_role.sql` — widens
  `kgrr_object_role_ck` on `ka_gochara_relationship_record` with `'av_qualifier'`
  (AM-7). Migration 1155 (applied) never edited; v1.0 vocabulary a strict subset.
- `platform/migrations/1205_gochara_inherited_frame_kind.sql` — adds
  `WHEN 'inherited' THEN frame_arg IS NULL` to `ka_gochara_frame_ok` (AM-8) via
  `CREATE OR REPLACE` (oid preserved; v1.0 arms byte-identical).
- **The flagged fold (the one thing beyond the amendment list's literal text):**
  the object-role vocabulary also lives in the *selector* validator
  `ka_gochara_object_selector_ok` (`1154_gochara_rule_path_registry.sql:252-261`),
  which AM-7's draft does not name. 1204 widens that one validator with the same
  single value — otherwise a P5 path could never SELECT the role its own records
  carry (contract internally inconsistent). The 1204 header labels this and gives
  a rollback path if the gate vetoes. **Judge: is the selector widening the right
  call, or should the selector stay v1.0 (and if so, how does a P5 path legitimately
  bind the qualifier)?**
- Wiring mirrors #2765: `migrate.ts` `PROTECTED_PUBLIC_SCHEMA_MIGRATIONS` += both;
  `deploy.yml`'s `gochara_contracts_schema_migration=true` window applies exactly
  1153-1157, 1204-1205 in ascending order; preflights byte-identical to the
  embedded gates; routine-runner refusal tested.
- Tests: `tests/unit/migrations/gochara_b6_v15_contract_static.test.ts` (11 static
  checks) and `tests/integration/gochara_b6_v15_migrations.db.test.ts` (8 live
  probes: `av_qualifier` record commits, `'not_a_role'` fails with
  `kgrr_object_role_ck`, selector admit/refuse/keep, `frame_ok('inherited',NULL)`,
  arg⇒FALSE, v1.0 arms unchanged, replay blocked). Reported green on disposable
  PG 17.10 and PG 15.17.

**What to judge (Exhibit 2):** Are both migrations correct, minimal, and safe to
run in the protected window on a live table? Is the CHECK-swap race analysis
(writer paused / no `'5.0'` write racing) sound? Is the selector widening in scope?

## Exhibit 3 — ORACLE_EXECUTION_MAP v1.1

File: `00_ARCHITECTURE/briefs/pravaha/measurement/ORACLE_EXECUTION_MAP_v1_0.md`
(version 1.1, commit `7e02d24f1`, branch `campaign/pravaha`). Adds the §A5.3 table
(:112-138): the A5.3 seam (`services/gochara_kernel/rule_registry.py`,
`evaluator.py` on `pravaha/a53-registered-writer`) covered by
`platform/python-sidecar/tests/l3/gochara/test_b6_oracles_a53.py` (PR #2819) —
11 REAL + 2 strict-xfail FINDINGs, 54 passed + 2 xfailed with Stream A's own a53
suites. Two oracles are honestly NOT yet executable on that seam and are mapped as
strict-xfail findings instead of being silently dropped:

- **B6-F16 / O-RP-1** — no admission-evaluation seam in the A5.3 modules yet
  (union-not-cascade + evidence_against attribution).
- **B6-F17 / O-P6-TARA** — P6 day-tier deferred (D1: `day_on_demand`; needs the
  AM-8/`1205` `'inherited'` frame fold — the Exhibit-2 dependency).

Mutation evidence (applied → RED → reverted, 2026-10-01): Saturn's 8th dropped
from the P2 adverse plan → O-RP-5a RED; node-aspect skip removed → O-RP-8 exact
count RED; dignity ordering reversed → O-RP-7 RED.

**What to judge (Exhibit 3):** Is the mapping honest (no oracle claimed REAL that
the suite does not actually execute)? Are B6-F16/B6-F17 legitimate deferrals with
named unblock conditions, and does the v1.5 trajectory close both? Is the mutation
evidence sufficient to call the suite a detector and not a mirror?

## Verdict shape requested

One verdict per exhibit (PASS / PASS-WITH-AMENDMENTS / REJECT), plus the AM-6 pick
(A/B/C) with the reason. Findings numbered; anything the gate refuses returns to
this stream with evidence and the item stays parked.
