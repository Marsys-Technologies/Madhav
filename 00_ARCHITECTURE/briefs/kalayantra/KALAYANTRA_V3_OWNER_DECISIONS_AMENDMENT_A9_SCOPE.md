---
title: KĀLA-YANTRA v3 owner decisions — Amendment A9 (scope: the close is rooted on the acceptance set; product depth kept; clean-up deferred)
version: 1.0
status: CURRENT
date: 2026-10-18
amends: KALAYANTRA_RELAUNCH_PLAN_v2_7.md §0 closure procedure (applied as written), the plan model's close chain (C-1 ← JOIN-ALL), K9-4a's dependency list, the V-* packet-exit items, Amendment A5 D-37 (children of findings), Amendment A8 §4 (packet-exit reviews)
precedence: where this amendment and any amended document disagree, THIS AMENDMENT GOVERNS.
changelog:
  - 1.0 (2026-10-18): created on the owner's approval of the revised scope proposal ("the updated plan is approved, please go ahead"), after the owner's check that quality, capability, features and depth are unaffected.
---

# Amendment A9 — scope

**Written for:** the cockpit session, the owner surrogate and the tracker.

## §1 · Basis

Plan v2.7 §0 defines the retained acceptance set: (i) Kāla serves `482012f1` end to end from a rebuilt, published layer; (ii) the Gochara 5.0 flip is sealed and served; (iii) certification mappings exist for every served Kāla asset; (iv) a guarded close. §0 step 1 says the `JOIN-ALL` / C-chain is **not** a scope root; step 3 says everything outside the closure of the roots is deferred with a re-entry condition and never counted as closed. The tracker nevertheless wires `C-1 ← JOIN-ALL ← every retained item`, which made every item, including process leftovers, part of the critical path. Measured on 2026-10-18: 173 open items, of which 61 lie outside the closure of the acceptance roots.

Reading the 61 one by one: about 45 are review follow-ups whose code is already merged (they complete under A7 D-46 as soon as the sweep runs); 6 are Tier-2 methods and 2 are the L5 hand-off, which are product depth; 3 are acceptance or quality checks that belong inside the closure; the rest are legacy clean-up and a predecessor campaign's paperwork.

## §2 · D-51 — the close is rooted on the acceptance set

1. `ACCEPTANCE_ROOTS_v3.json`: (i) `K9-4b` and `K9-6`; (ii) `J-6l`, `J-5s`, `V-J6`; (iii) `K8-REG`, `K-CERT`; (iv) `V-K9` then `C-1 → C-2 → C-3 → C-4`. `JOIN-ALL` is removed as a dependency of `C-1` and marked `not_applicable: superseded by ACCEPTANCE_ROOTS_v3`.
2. `CLOSURE_v3.json` is computed from those roots over `depends_on`, deterministically (two runs, one hash), as §0 step 2 prescribes. Items inside are critical path. Items outside are deferred under §4, never counted as closed.
3. The tracker headline counts implemented and activated items over the closure's item count; deferred items are listed separately with their re-entry conditions.

## §3 · D-52 — product depth stays in the campaign

1. **Tier-2 methods** (`D-T2`, `J-7`, `J-7-a63`, `J-7-b61`, `J-7-n-t2`, `L0-K`) and the **L5 hand-off** (`J-7b`, `J-7b-b62`) are the post-flip phase of the campaign: they depend on `J-6l` and are built, reviewed and merged after the flip is served. They are not deferred. `D-T2`'s conditional approval (PRE-D-T2-v2) stands.
2. **Live acceptance of the served layer** (`K9-6`), the **final whole-layer review** (`V-K9`) and the **avadhi integrity check** (`K-AVADHI-C`) are in the closure. `K-AVADHI-C` is unparked with its brief's condition intact.
3. **Doctrine findings are always items.** A review finding about doctrine, a classical source, a served value or a calculation becomes a tracked item in the closure. A finding about process, test hygiene or tooling becomes a comment on the pull request (A8 §3.2). This replaces A5 D-37's child-item rule.

## §4 · D-53 — deferred, with re-entry conditions

Parked (`ky park --as steward --detail "deferred by A9; re-entry: …"`), never counted as closed:
- Legacy clean-up after the flip: `J-7a`, `J-7a-a62`, `J-7a-pr3099`, `KR-1`, `KR-2`. Re-entry: after `V-J6` is accepted and the served layer has run one week on `5.0`.
- Predecessor paperwork: `J-8`, `J-8-b63`, `J-8-j3`, `J-8a` (Pravāha close report and archive). Re-entry: at campaign close, as documentation.
- Rehearsal census: `K9-5`, `K9-5-NB-01`. Re-entry: when Suvarṇa schedules its certification census.
Marked `not_applicable` with the reason stated: `K-CERT-2` (superseded as complete by Suvarṇa PR #3435), `W4-SAFETY-N01` and `W4-SAFETY-N02` (superseded by the scoped backup and the executed small test), `KA3B-N1` and `KA3B-N2` (process notes), `OPS-NB-03` (fleet tooling), `JOIN-ALL` (§2.1).
`D-GOCHARA-TIMEOUT` and `J-GOCHARA-TIMEOUT` are decided and closed by the surrogate on the merged evidence; they are not deferred.

## §5 · D-54 — packet-exit reviews

`V-K3b`, `V-K5`, `V-K6`, `V-KA` and `V-VC` are `not_applicable: satisfied by the per-change independent reviews under D-OWNER-TESTS-20261016` (A8 §4). `V-K9` (the rebuilt layer against the exit criteria) and `V-J6` (the flip) remain and are run by the normal reviewer under criterion v2. `K9-4a`'s `depends_on` drops the retired `V-*` entries and keeps `D-FLIP`, `J-6l`, `V-J6`, `K9-23`, `V-K9`.

## §6 · D-55 — tooling budget

Once the A8 fast-lane and code edits are merged, fleet tooling and governance work is limited to 10% of launched jobs and to changes that remove a measured blocker. The daily report states the share.

## §7 · What this does not change

No code in `main` is removed or weakened. No review of a code change is removed. The 16 required checks are unchanged. The owner's kept rules and the personal-data handling are unchanged. The Wave 4 chain and the Wave 2 path to `K9-4b` are unchanged.

## §8 · Success (at the next daily report)

| Measure | Target |
|---|---|
| Closure item count (denominator) | about 200, from 264 |
| Open critical items | about 110, from 173 |
| Deferred items listed with re-entry conditions | every item in §4 |
| Open review-finding children with merged code still uncounted | 0 after the D-46 sweep |
| New child items from process or hygiene findings | 0 |
