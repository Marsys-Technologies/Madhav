---
artifact: L1_STATE.md
canonical_id: NIRMANA_V21_L1_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L1
layer: L1 — Gaṇita
owner: the L1 session (this file is yours alone — charter C5)
last_updated: 2026-09-05 — C8 v2.3 cycle 2; ga_positions W2 acceptance events LIVE, E-gate cond 2 open
---

# L1 — Gaṇita — SESSION STATE

Rebased onto the CONDUCTOR stub (its bootstrap facts and standing rulings retained verbatim below).
Charter C9: this file is your memory — update it every loop, commit it with
every PR and at every milestone, so re-pasting your prompt into a fresh session is safe at any
moment.

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → this file → `git fetch origin main` →
your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 (run-slot claims, freeze-ordering acks, monster scheduling)
- **Adjudication:** open a new issue labeled `nirmana-adjudication`, then keep working (C3)
- **Migration range:** 650–659 (yours alone, collision-free by construction)
- **Branch namespace:** `codex/nirmana-l1-*` · **PR title prefix:** `L1:`
- **Worktree:** `~/nirmana-s/l1`
- **Standing ruling D-CND-01 (read before your first Conform-stage check):** a `count(*) = N` is
  permitted only as a conjunct of something that can fail on corruption it cannot see — a total
  content fingerprint, or named invariants (contiguity, tiling, distinctness, cross-table
  FULL-JOIN consistency, NULL/range guards). Alone it is forbidden (C12). `expected_volume_formula`
  is REQUIRED when a count equality is the volume assertion; not required alongside a total-content
  digest. Full reasoning + the L0 evidence: `CAMPAIGN_STATE.md` → CONDUCTOR standing audit A-01.
- **Freeze predecessor:** L0 Brahmagyan must be frozen before your W6 ceremony (C2; asset work is never held)

## Position

**L1-W3 IMPLEMENT — in flight, under C8 v2.3 supervised-cycle model.** W1 + W2 COMPLETE (19/19
routed). #1736 (evidence-spine generalisation), #1740 (W1+W2 docs), #1756 (W3 registry truth) all
**MERGED** since the last heartbeat — the W2 acceptance-event hold (#1715) is now clear to act on
next cycle. Only one L1 PR remains open: **#1766** (ga_vargas birth-instant + delete-grain fix).

**Cycle 1 (this session, first under C8 v2.3):** PR #1766 was CLEAN and un-queued at cycle start;
armed auto-merge, then Conductor's fleet-wide diagnosis (issue #1713, 13:32Z) surfaced that it had
actually already been ejected from the merge queue by a NEW merge-group gate (Nirmana analysis-
layer pin check, landed via #1815 after this PR's branch checks last ran) — `ga_vargas_writer.py`
changed in this PR, so L1's `writer_inventory_sha256` in the committed pin file went stale. Fixed
per Conductor's posted instructions: rebased onto origin/main, regenerated **only L1's slice**
(`--layer L1 --convergence-commit b71ee4af` — this branch's own reviewed HEAD; L0/L2/L3/L4/L5
untouched byte-for-byte), which required a real Postgres connection for `load_frozen_manifest_assets()` —
reused the **already-running shared cloud-sql-proxy** on `127.0.0.1:5433` (did not spawn a
redundant one; attempted spawn correctly failed on port-in-use and left nothing behind) with the
`amjis-pipeline-db-url` secret (read-only manifest lookup, no write path touched). Had to
GraphQL `dequeuePullRequest` the stale queue entry before GitHub would accept the force-push
(protected-branch rule blocks pushing to a branch currently in the merge queue). Re-armed
auto-merge; `mergeStateStatus: BLOCKED` (checks re-running on the new commit) as of this write —
next cycle re-verifies with `is:queued` per the charter's exact-claim requirement.

## CYCLE 2 (C8 v2.3) — canary W2 acceptance events LIVE

**PR hygiene first (per contract):** re-verified #1766 and #1827 with `is:queued` — neither queued
yet, but neither RED nor DIRTY either; both `mergeStateStatus: BLOCKED` with checks still running
(all green so far on #1766: TypeScript/DB-integration/governance gates all `pass`, only 2-3 slow
jobs still `pending`). Nothing actionable — not stuck, just mid-flight. Left as-is for next cycle
to re-verify.

**The unit of work: proved the W2 acceptance-event submission mechanism end-to-end on the canary,
`ga_positions`.** The hold from #1715 cleared last cycle (its three PRs merged), but nothing had
actually exercised the executor HTTP path for L1 yet. Rather than batch-submitting all 19 assets
blind, did exactly what the charter's own canary discipline asks (W4's "prove the cross-layer gate
on ga_positions first" — the same principle applies here one step earlier):

1. Computed `registry_fingerprint_sha256` + `analysis_digest` for `ga_positions` using the REAL
   deployed code, not a reimplementation — imported `canonicalRegistryContractDigest`,
   `registryContractFingerprintInput`, `canonicalNirmanaAssetAnalysisDigestForRegistryRow` directly
   from `definitions.ts` via a throwaway `tsx` script (never committed, deleted after use),
   querying the live registry+frozen-manifest join myself with a plain `pg.Client` rather than
   pulling in the module's writer-pool machinery. Verified first that the deployed Cloud Run
   revision's `commit-sha` label (`75ac19c66…`) has byte-identical `definitions.ts` +
   both generated pin/digest files to current `origin/main` (diff empty), so this local
   computation is provably what production would compute too — not a guess.
2. Minted an executor-scoped OIDC token (`amjis-nirmana-executor@…`, `--include-email` — the
   documented trap in CAMPAIGN_STATE.md that produces a silent-403 if omitted) and probed the route
   with an intentionally invalid body first: **HTTP 400** (proves auth passed; a 403 would have
   meant it hadn't) before ever sending real data.
3. Submitted `asset_analysis_accepted` then `optimization_verdict_accepted` for `ga_positions`
   (route `rebuild_only` → verdict `examined_and_already_efficient`, action `no_change`,
   `output_contract: digest_identical` — the writer needs no code change, only the registry-only
   fixes already landed in #1756). Both **HTTP 201 created**.
4. Re-ran the E-gate batch query: `ga_positions` now reads `w2_analysis=t w2_verdict=t gate=OPEN-PENDING-PIN`
   — first-ever L1 asset to clear E-gate condition 2. **The mechanism works.**

**Decided against batching the remaining 18 in this same cycle** (D-L1-22) — one bounded unit per
the C8 v2.3 contract, and the verdict payload for each of the other 18 needs its own accurate
`evidence_refs`/`summary` drawn from `L1_W2_DECIDE_v1_0.md` §2, not a copy-paste of the canary's.
Next cycle: batch the remaining 10 `rebuild_only` assets first (same `examined_and_already_efficient`
shape, low risk of payload error), then the 8 `changed` assets (need `verdict: correct` /
`optimize_and_correct` and a `correctness_change` output_contract, one per asset's actual MUST
finding), then `ga_prashna` last (still `rebuild_only`/`examined_and_already_efficient` — the R-1
dormancy is a registry `data_disposition` field, not a different verdict category).

## CYCLE 3 (C8 v2.3) — remaining 10 `rebuild_only` W2 acceptance events LIVE

**PR hygiene:** `is:queued` shows #1766 now genuinely queued (good — Conductor or the queue
itself must have picked it up after checks finished green). #1827 (state PR) still `UNKNOWN`/
checks running, all green so far, nothing RED/DIRTY. Nothing to fix.

**The unit of work: batched the remaining 10 `rebuild_only` L1 assets' W2 acceptance events** —
`ga_nakshatra`, `ga_sensitive`, `ga_sensitive_degree`, `ga_strength`, `ga_structural`, `ga_yoga`,
`ga_vichara`, `ga_sade_sati`, `ga_ayurdaya`, `ga_prashna`. Same mechanism the canary proved:

1. Reused the throwaway `tsx` digest script (definitions.ts unchanged between the deployed sha
   and current `origin/main` — re-checked before reuse) to compute `registry_fingerprint_sha256`
   + `analysis_digest` for all 10 in one DB round trip; deleted the script immediately after.
2. Built all 20 request bodies via a Python generator script (not hand-typed, not templated
   through nested shell quoting) with each asset's own `evidence_refs` (correct W1 batch letter:
   B for nakshatra/sensitive/sensitive_degree, C for strength/structural, D for
   yoga/vichara/sade_sati, E for ayurdaya/prashna) and its own one-line summary drawn from
   `L1_W2_DECIDE_v1_0.md` §2's actual per-asset rationale — never a copy-paste of the canary's.
   **Read the generated JSON bodies before sending anything real**, specifically because the
   evidence route's `ON CONFLICT (campaign_id, definition_revision, idempotency_key) DO NOTHING`
   means a wrong payload submitted under a given idempotency_key would silently freeze that
   mistake in place — a later correct resubmission under the same key would no-op, not overwrite.
3. Same verdict shape as the canary for all 10: `examined_and_already_efficient` /
   `no_change` / `digest_identical` — every one of these 10 is `rebuild_only` (writer
   unchanged), including `ga_prashna` (R-1 dormancy is a registry `data_disposition` field, not a
   different verdict category — confirmed unchanged from the plan).
4. All 20 POSTs (10 assets × 2 events) returned **HTTP 201 created**. Zero failures, zero retries.
5. Re-ran the E-gate batch query: **all 11 `rebuild_only` L1 assets** (canary + these 10) now read
   `w2_analysis=t w2_verdict=t`. `ga_positions` stays `OPEN-PENDING-PIN` (T0, no unfrozen
   ancestors); the other 10 read `BLOCKED-ANCESTORS` as expected (condition 2 clear, condition 1
   still waiting on `ga_positions` itself to freeze — that is the DAG working as designed, not a
   defect).

**Remaining W2 acceptance-event work: the 8 `changed` assets** (`ga_vargas`, `ga_dashas`,
`ga_panchanga`, `ga_condition`, `ga_tajaka`, `ga_transit_anchors`, `ga_medical`, `ga_vastu`) —
deliberately held for their own cycle rather than folded in here (D-L1-23): their verdict is
`correct` or `optimize_and_correct` with `output_contract: correctness_change`, a materially
different and higher-stakes claim than `examined_and_already_efficient`, and each needs its own
MUST-finding-specific summary, not a templated one. `ga_vargas` additionally has an OPEN PR
(#1766, its writer fix) that must be MERGED+DEPLOYED first — submitting `changed` acceptance
evidence against a not-yet-deployed writer fix would bind the analysis to a `source_ref` commit
that isn't actually running in production yet, which `assertNirmanaGitCommitMatchesDeployment`
would reject anyway (source_ref must equal `NIRMANA_DEPLOYED_SHA`).

## CYCLE 4 (C8 v2.3) — `ga_positions` blast-radius statement (C13/D-NATIVE-05)

**PR hygiene:** #1766 and #1827 both clean — nothing to fix (checked `is:queued`/checks before
starting; no change since cycle 3's note beyond checks finishing).

**Unit of work: produced the C13 blast-radius statement for `ga_positions`/`chart_facts`** —
mandatory before any dispatch per D-NATIVE-05 ("no session dispatches any build whose asset has
populated downstream tables... check it yourself") and C13 ("every W2 route decision must include
a downstream blast-radius statement"). `ga_positions` is `OPEN-PENDING-PIN` on the E-gate (both
conditions 1+2 clear since cycle 2) but nothing had actually cleared it for W4 dispatch yet.

1. **Cascade closure** (`cascade_check.sql -v table=chart_facts`): one child,
   `chart_fact_identity` (L1, **IN-LAYER**) — no cross-layer cascade, no adjudication needed.
2. **No-FK referrer**: `chart_facts_history` (`fact_id` text column, no FK) — but it is a genuine
   append-only audit/change-log table (`operation`/`old_value`/`new_value`/`build_id` columns) whose
   PURPOSE is to outlive the current-state rows it describes, and it holds **0 rows for the
   canonical chart** right now. Not a real orphan risk today; recorded as an honest "populated: no"
   rather than assumed safe from the table's name alone.
3. **Scoped the real number, not the naive table-wide one.** The raw cascade query reports
   `chart_fact_identity` as 270,471 rows *campaign-wide*; that is not what a `ga_positions` rebuild
   for this chart touches. Verified `ga_positions_writer.py`'s actual delete scope
   (`_idempotency.py`'s `replace_prior_chart_facts`: `WHERE chart_id = %s AND fact_category =
   ANY(%s) AND ayanamsha_id = ANY(%s)`, never a bare table truncate) and the writer's real
   `fact_category` set (`graha_position`, `graha_sign_attributes`). Measured directly: **530
   `chart_fact_identity` rows** (`chart_fact_identity_fact_id_fkey ... ON DELETE CASCADE`, PK =
   `fact_id`, a 1:1 parse-decoration companion row per fact) would cascade-delete-then-immediately-
   reinsert for chart `482012f1`'s positions categories — the writer's own in-layer replacement of
   its own companion rows, not third-party data.
4. **Verdict: dispatch is CLEAR.** No cross-layer boundary crossed, no adjudication issue needed.
   D-NATIVE-05's hold was scoped to "until WP-6 is live" — confirmed live (Conductor's 05:01Z
   broadcast + C13's own text describing it as already enforcing, not "building now") — so the
   governing rule for this dispatch is the standing C13 discipline (blast-radius statement + fresh
   snapshot + `--acknowledge-destroys` when anything would be destroyed), not the blanket hold.

**Decided NOT to also claim a slot and dispatch in this same cycle** (D-L1-24) — checked the
coordination issue (#1713) live rather than assuming: **L3 claimed a slot for `ka_graha_sancara`
and L5 claimed one for `mi_vistara`, both within the last few minutes** (14:06–14:07Z), so at most
1 of 3 slots is free right now (and the day-old ledger note says treat L0 as potentially occupying
one too — effectively 0–1 free for L1–L5). Claiming the actual dispatch is next cycle's unit:
confirm a free slot on the ledger, reuse L5's just-taken fresh snapshot
(`cloudsql-backup:1788617073802`, confirmed SUCCESSFUL 2026-09-05T14:04:33Z) if still fresh enough
by then or take a new on-demand one, post the SLOT CLAIM comment, dry-run
`dispatch_nirmana_campaign_wave.py`, review the manifest digest, then `--commit
--acknowledge-destroys` (530 in-layer rows) with the snapshot ref.

## E-gate (C2/C10) — measured live 2026-09-05

All five L0 ancestors of L1 are already `asset_frozen` (`bg_kp_sublord_division`, `bg_nakshatra`,
`bg_panchanga`, `bg_prashna_rules`, `bg_reference`), so L1 is gated only on its own DAG.

| tier | assets | unfrozen ancestors |
|---|---|---|
| T0 | `ga_positions` | **0 — conditions 1+2 OPEN; gate=OPEN-PENDING-PIN (cond 3: verify pins, claim slot, dispatch)** |
| T1 | `ga_ayurdaya`✅ `ga_dashas` `ga_nakshatra`✅ `ga_panchanga` `ga_prashna`✅ `ga_sensitive`✅ `ga_sensitive_degree`✅ `ga_transit_anchors` `ga_vargas` | 1 |
| T2 | `ga_strength`✅ | 2 |
| T3 | `ga_condition` `ga_tajaka` | 3 |
| T4 | `ga_medical` `ga_vastu` | 4 |
| T5 | `ga_structural`✅ | 7 |
| T6 | `ga_sade_sati`✅ `ga_yoga`✅ | 8 |
| T7 | `ga_vichara`✅ | 9 |

✅ = condition 2 (`w2_analysis`+`w2_verdict`) now clear as of cycle 3; still `BLOCKED-ANCESTORS`
on condition 1 (waiting on `ga_positions` to freeze, per the DAG). Unmarked = the 8 `changed`
assets, condition 2 still open (their own cycle, per D-L1-23).

Canary `ga_positions`: **cond 1 ✅ · cond 2 ❌ (#1715 → PR #1736) · cond 3 ✅.**
Manifest waves: W0=1, W1=9, W2=3, W3=3, W4=2, W5=1.

## Asset table (19 assets)

Live counts vs declared floor, canonical chart `482012f1`. Routes are W2 *proposals* from W1 —
none accepted yet (blocked on #1736).

| asset_id | live / floor | proposed route | headline W1 finding |
|---|---:|---|---|
| ga_positions | 890 / 50 | rebuild_only | layer root; canary |
| ga_vargas | 23,542 / 22,092 | **changed** | **MUST: longitudes computed for the wrong instant (F-A)** |
| ga_dashas | 483,859 / **536,471** | rebuild_only | floor decomposed to 5 named causes, sums exactly (F-A) |
| ga_nakshatra | 2,847 / 1,802 | rebuild_only | `ganita_nakshatra_get` does not serve it (F-B18) |
| ga_panchanga | 437 / 221 | **changed** | **MUST: `*_arambha_iso` stores the anga END (F-B24)** |
| ga_sensitive | 8,565 / **8,610** | rebuild_only | deficit = floor-vintage mismatch, not a defect (F-B) |
| ga_sensitive_degree | 275 / 0 | rebuild_only | derives to 335; `count_sql` omits 60 served rows (F-B) |
| ga_strength | 13,621 / 11,936 | **changed** | **MUST: ṣaḍbala selector still wrong on 2 of 3 charts (F-C)** |
| ga_structural | 98,542 / 77,821 | rebuild_only | owns argala 41,760 — unconsumed; undercounts self ~5,157 (F-C) |
| ga_condition | 2,880 / 2,880 | **changed** | **MUST: `varga_dignity_composite` NULL on 135/135 served (F-C)** |
| ga_yoga | 63 / 5 | **changed** | citations exist (233/233) but no surface joins them (F-D1) |
| ga_vichara | 8,249 / 0 | rebuild_only | real and mis-labeled: DRAFT → CURRENT (F-D) |
| ga_sade_sati | 6,287 / **11,019** | rebuild_only | reconciles to the row; stale floor from a since-fixed writer (F-D) |
| ga_transit_anchors | 45 / 45 | **changed** | AV transit gating does NOT live here — serve-time TS (F-D) |
| ga_ayurdaya | 130 / 0 | rebuild_only | `get_ayurdaya.ts` omits `fact_value_jsonb` (F-E) |
| ga_medical | 45 / 45 | **changed** | **MUST: build-fatal gate passes for a wrong reason (F-E)** |
| ga_vastu | 40 / 40 | rebuild_only | highest leverage: L0 direction remedies never joined (F-E) |
| ga_tajaka | 240 / 240 | rebuild_only | floor is a wall-clock literal; already wrong on 2/3 charts (F-E) |
| ga_prashna | 0 / 0 | **dormant disposition** | R-1: facility is live-mounted; 5 orphaned served rows (F-E) |

Cross-cutting: **0/19 carry `integrity_check_sql`**; `expected_volume_formula` NULL on 6;
`ga_vichara` is `catalog_status=DRAFT` with 8,249 live rows.

## Decisions log

- **D-L1-1** — Worktree `~/nirmana-s/l1` from `origin/main` `20323fae4`; state rebased onto the
  Conductor stub. Basis: C4/C9.
- **D-L1-2** — Found the evidence spine hardcoded to L0 (4 sites); filed **#1715** rather than
  touching a Conductor-owned lib (C5). Ruled Option A, **L1 assigned to author**. → PR #1736.
- **D-L1-3** — Three assets below floor. Per C12 ("derive, never pick") each was assigned a
  first-principles derivation before routing, not resolved as "stale floor". All three now
  derived: `ga_dashas` (5 causes, sum exact), `ga_sade_sati` (reconciles to the row),
  `ga_sensitive` (floor-vintage mismatch). **None is a build regression.**
- **D-L1-4** — C2 condition 3 verified green for L1: 19/19 registry pins match the frozen manifest
  (self-testing checker: reproduces all 128 manifest fingerprints before it will report), and
  `provenance_inventory --check` exits 0. Incidental campaign-wide finding reported to the
  Conductor: `bg_parihara_rules` is the one drifted pin (L0-owned, untouched).
- **D-L1-5** — Found the `integrity_verified` detector cannot execute chart-scoped SQL (81 assets,
  L1–L5). Filed **#1727**; **closed as duplicate of L4's #1723**, whose ruling (D-CND-03) is
  *stronger* than my proposal — chart-partitioned `NOT EXISTS` invariants, no bind placeholders.
  Correction recorded on the issue rather than left standing. **L1 owns authoring 19 real
  integrity contracts** as W3 work.
- **D-L1-6** — Recorded that fixing the detector unblocks but does not EARN the signal: with
  `integrity_check_sql` NULL the fallback passes on `count > 0`, so `ga_dashas` would assert
  integrity on `483,859 > 0` (§N.8).
- **D-L1-7** — Scope sweep for further L0-only assumptions came back clean apart from #1723
  (`accepted_rebuild_observed` is already scope-aware, `definitions.ts:2277-2278`). Also: the
  legacy `run_l1_ganita_build.py` bypasses the orchestrator and must NOT be used for W4 — all 19
  L1 writers are confirmed orchestrator-native (`@register` + `WriterBase`).
- **D-L1-8** — Found `VERIFICATION_RESCALE` scores `single` (0.60) and its own declared alias
  `single_pass` (0.85) differently, on 85.2% of the chart's facts. Filed **#1729** (D-SALIENCE,
  L1→L2 feed).
- **D-L1-9** — **Deliberately did NOT do the mandate's vocabulary normalization.** Doing it first
  would silently demote 10,316 rows 0.85 → 0.60 — a salience regression shipped as a cosmetic
  cleanup (plan §6.2 "never silently better", in reverse). **HELD on #1729.**
- **D-L1-10** — W1 complete, 19/19, via five read-only subagents on disjoint asset sets. ~139
  findings (F-A1…F-E28). Deliverables `L1_W1_ANALYSIS_BATCH_A…E.md`. Every below-floor asset got
  a derivation; every uncertainty is registered as uncertainty rather than resolved by guess.

- **D-L1-11** — W2 routes assigned on one question: *does the rebuild need changed writer code?*
  8 `changed`, 11 `rebuild_only`. **`verified_reuse` rejected for all 19** — it requires proven
  integrity, and 0/19 carry `integrity_check_sql`, so claiming it would be an unearned signal (§N.8).
  Five MUST findings are serving-side; their assets stay `rebuild_only` because routing them
  `changed` would assert a writer change that does not exist.
- **D-L1-12** — Independently re-verified F-A1 (`ga_vargas`) from production before broadcasting it,
  rather than relaying a subagent claim into a cross-layer alarm. Lagna Δ **0.0000°**; Sun Δ 0.2324°
  and Moon Δ 2.7169° — two bodies with 12× different daily motion, both off by the same **0.229 day
  = 5h30m**. Filed as cross-layer notice **#1747** with a sequencing question for L2–L5.
- **D-L1-13** — Found the frozen definition can never be superseded again (174 events / 11 runs block
  it; no side door). Consequence: **`depends_on` is immutable campaign-wide**, so all 11 L1 DAG
  corrections are NEVER-LATER-documented. Filed **#1744** — including the correction that my first
  read ("any registry change bricks the asset") was **wrong**: only `layer` and `depends_on` are
  pinned against the manifest, so D-CND-03's integrity-contract work is unaffected. Mitigating the
  one DAG defect with live consequences (`ga_dashas`/`ga_vargas` MVCC race) by **sequential
  single-asset dispatch** at W4 rather than by pretending the graph is accurate.
- **D-L1-14** — #1729 ruled: L2 implements, L1 supplies weights. Delivered a 13-member proposal, and
  argued the table's **shape** is wrong as well as its numbers — 5 statuses describe the *absence* of
  a value (`floored`, `not_defined_for_nodes`, `scope_cap_sentinel`, `skipped_malformed_source`,
  `external_computation_required`) and should be EXCLUDED from salience rather than weighted;
  scoring an N/A at 0.60 is a category error, not caution (§N.7 item 6).
- **D-L1-15** — **Dropped** the mandate's status-vocabulary normalization from W3 scope entirely
  (superseding the D-L1-9 hold). Once #1729 makes aliases resolve through `verification_vocab`,
  which spelling a writer emits stops mattering, so the cleanup has no purpose. Recorded as
  cosmetic-backlog, not as blocked work — the Conductor was explicit that L1 should hold nothing
  for it.

- **D-L1-16** — W3 batch 1 (**PR #1756**, migration 650): registry truth — 3 `count_sql`
  completions (categories written AND served but counted by nobody), 11 floors set to the measured
  minimum across all three built charts, 2 `target_table`, `ga_vichara` DRAFT→CURRENT, and
  `ga_prashna`'s R-1 dormancy made machine-readable. Dry-run against production inside
  BEGIN/ROLLBACK before shipping. Floors deliberately NOT set for the 6 assets whose routed fix can
  still change their count — a test asserts that, so a later edit cannot quietly fill them in.
- **D-L1-17** — **Found and fixed a defect I had just introduced, plus a pre-existing one.** L5's
  #1757 revealed the seed *executes* `expected_volume_formula`. My first draft used
  `ROWS_PER_AYANAMSHA` / `DIRECTIONS` / `BHAVA_CUSPS` — all outside the seed's 16-name
  `ALLOWED_VARS`, so it would have hard-failed `runSeed`. Rewrote as `<literal> * AYANAMSHAS`
  (inside the grammar, and evaluating to the true live count). Auditing all 128 assets against that
  grammar then found **three formulas on `main` that already break `runSeed`**: `ga_vichara` (mine,
  fixed), `bg_kp_sublord_division` (L0) and `bo_pratijna` (L2) — reported on #1757, not touched.
- **D-L1-18** — W3 batch 2 (**PR #1766**): `ga_vargas` computed every graha for an instant 5h30m
  after birth. PyJHora's own docstring states the two-JD convention; the writer passed the local-time
  JD to `sidereal_longitude`, which requires UTC. **Verified against the L1 authority before writing
  the fix**: `jd_ut - tz/24` reproduces `chart_facts` Sun 291.9626 and Moon 327.0552 EXACTLY.
  Scope checked not assumed — `ga_dashas` uses the same primitive but converts correctly, and no
  other `ga_writer` builds a JD this way. Four tests, two mutation-proven. F-A2/F-A3 deliberately
  deferred to W3 batch 3 (they need a migration) so `ga_vargas` rebuilds once, not twice.
- **D-L1-19** — #1744 ruled (D-CND-09): `depends_on` and `layer` immutable, everything else mutable
  before acceptance; sequential single-asset dispatch **granted** for the `ga_dashas`/`ga_vargas`
  race, as two separate slot claims. Posted L1's **11 DAG corrections in both-directions form** to
  #1734 for the Phase-Z register, with per-row verification status — 4 re-derived from writer source
  by me, the rest carried from W1 with `file:line`. Register note added: three L1 assets declare
  `ga_positions` and then re-derive positions, which is §N.5 inverted *within* L1 — and is exactly
  how `ga_vargas` came to hold a different D1 from the authority it declares a dependency on.
- **D-L1-20** — #1729 ruled: delivered the 13-member weight proposal, arguing the rescale table's
  **shape** is wrong as well as its numbers (5 statuses describe the absence of a value and should
  be EXCLUDED from salience, not weighted). #1750 opened to hand L2 three verified serving-side
  defects in its own write-set — the ṣaḍbala selector (still wrong on 2 of 3 charts; the 2026-07-28
  fix and its re-verification were both run on the only chart where it cannot manifest), the AV
  multiplier saturating at 1.15 for 12/12 houses because SARVA bindus (23–34) feed BHINNA bands
  (0–8), and the formula-version label. All three re-verified by me before filing.

- **D-L1-21** — C8 v2.3 cycle 1 PR hygiene: #1766 ejected from the merge queue by the new
  cross-layer pin gate (#1815) because this PR's own writer change (`ga_vargas_writer.py`) moved
  L1's `writer_inventory_sha256`. Fixed via `--layer L1` regeneration (Conductor-authored generator,
  #1814 per-layer mode) rather than whole-file regen, which would have falsely restated
  L2–L5's `convergence_commit` as reviewed by me. Used the campaign's already-provisioned
  `amjis-pipeline-db-url` read secret through the shared cloud-sql-proxy already running on this
  machine (127.0.0.1:5433) — read-only manifest lookup only, no write-path credential use, no new
  proxy process spawned. Required a GraphQL `dequeuePullRequest` before the protected-branch rule
  would accept the rebase+pin-regen force-push.

- **D-L1-22** — C8 v2.3 cycle 2: proved the W2 acceptance-event mechanism on the canary
  (`ga_positions`) before batching all 19 (full account in the CYCLE 2 section above).
  `asset_analysis_accepted` + `optimization_verdict_accepted` both HTTP 201; E-gate condition 2 now
  reads true for `ga_positions` (`gate=OPEN-PENDING-PIN`). Used my own gcloud identity's
  `serviceAccountTokenCreator` grant on `amjis-nirmana-executor@...` — the native-provisioned,
  campaign-sanctioned path per CAMPAIGN_STATE.md's P3 credential resolution, no new IAM, no key
  file. `registry_fingerprint_sha256`/`analysis_digest` computed with the real TypeScript functions
  (imported, not reimplemented) to guarantee byte-for-byte agreement with the server's own
  independent recomputation.

- **D-L1-23** — C8 v2.3 cycle 3: batched the remaining 10 `rebuild_only` L1 assets' W2 acceptance
  events (full account in the CYCLE 3 section above). All 20 POSTs HTTP 201, zero retries.
  Deliberately held the 8 `changed` assets out of this batch — their verdict category
  (`correct`/`optimize_and_correct`, `output_contract: correctness_change`) and per-asset MUST
  summaries are a materially different, higher-stakes claim than the templated
  `examined_and_already_efficient` shape, and `ga_vargas` specifically cannot be submitted at all
  until #1766 merges and deploys (`assertNirmanaGitCommitMatchesDeployment` requires `source_ref`
  to equal the currently-deployed commit).

- **D-L1-24** — C8 v2.3 cycle 4: produced `ga_positions`' C13/D-NATIVE-05 blast-radius statement
  (full account in the CYCLE 4 section above) — cascade closure IN-LAYER only (`chart_fact_identity`,
  530 rows scoped to this chart's positions categories, verified against the writer's actual delete
  SQL rather than the naive table-wide cascade-check count), no-FK referrer (`chart_facts_history`)
  genuinely empty for this chart. Dispatch is clear; no adjudication needed. Deliberately did NOT
  also claim a slot/dispatch this cycle — checked #1713 live and found L3 + L5 had claimed slots
  within the last few minutes, leaving 0–1 free. One bounded unit per C8 v2.3; the slot-claim +
  dispatch is next cycle's work once occupancy is re-checked fresh.

## Held items

- ~~All W2 acceptance events~~ — **hold CLEARED.** 11/19 (`ga_positions` + all 10 `rebuild_only`)
  submitted and confirmed live (D-L1-22, D-L1-23). Remaining 8 (`changed` assets) are unheld work
  for a future cycle, gated in practice by `ga_vargas` needing #1766 merged+deployed first (its
  `source_ref` must equal the deployed commit).
- **All W5 `integrity_verified`** — held on L4's #1723 Part B (detector placeholder guard) landing.
- ~~Status-vocabulary normalization~~ — **no longer held; dropped from scope** per D-L1-15.
- No upstream C6 capability holds: L0 declared none.

## CAPABILITIES LANDED

Charter C6 — announced here on `main`; consumers poll this section. **Nothing below is LANDED yet**;
each line names the PR it lands with, so a downstream session can tell "announced" from "available".

| capability | consumers | lands with | status |
|---|---|---|---|
| Layer-generic analysis-receipt spine (unblocks C2 cond 2 for all of L1–L5) | L2 L3 L4 L5 | PR **#1736** | IN REVIEW |
| `chart_divisionals` longitude correction — **~22% of varga sign assignments change on rebuild** | L2 L3 L4 | `ga_vargas` W3 | ANNOUNCED (#1747) |
| D-SALIENCE source-fact contract — exact `fact_category` names, live counts, and the vargottama multiplier-vs-increment units trap; plus the finding that **cancellation modifiers have no L1 source at all** | L2 (salience completion) | published now | **AVAILABLE** — `L1_W1_ANALYSIS_BATCH_C.md` |
| `ga_condition.varga_dignity_composite` populated (NULL on 100% today) | L2 | `ga_condition` W3 | ANNOUNCED |
| 19 L1 `integrity_check_sql` contracts (D-CND-03) | campaign verification | W3 | ANNOUNCED |

**L1 consumes no new upstream capability** — L0 declared none, and #1723's detector guard is a gate
L1 must satisfy rather than a feature it consumes.

## Cost ledger

| item | wall-clock | notes |
|---|---|---|
| bootstrap + grounding + 3 blocker analyses | ~35 min | E-gate, floors, pins all measured live |
| W2 DECIDE (19 routes, 139 findings) | ~20 min | incl. 2 further cross-layer findings |
| W3 batch 1 — registry truth (#1756) | ~35 min | incl. production dry-run + mutation-tested guards |
| W3 batch 2 — ga_vargas instant (#1766) | ~25 min | incl. live proof against the L1 authority |
| W1 ANALYZE (19 assets, 5 parallel subagents) | ~21 min wall / ~1.2M subagent tokens | fully parallel |
| PR #1736 (campaign critical path) | ~45 min | incl. generator, tests, live 6-layer acceptance |

## Heartbeat

- 2026-09-05 — **W1 + W2 COMPLETE; W3 in flight.** PR #1736 (critical path, in review) + #1740 (W1 docs) open.
  Issues: #1715 ruled→authoring, #1729 ruled→weights delivered, #1744 + #1747 filed, #1727 closed as
  dup of #1723; #1744 ruled and closed. PRs open: **#1736** (critical path, awaiting Conductor
  merge), #1740 (W1+W2 docs), #1756 (registry truth), #1766 (ga_vargas instant). **No slot
  claimed** — nothing is dispatchable while C2 cond 2 is shut, and holding a slot idle is
  forbidden (C5).
- 2026-09-05T13:42Z — **CYCLE 1 (C8 v2.3).** Confirmed no `NIRMANA_HOLD`. Found #1736/#1740/#1756
  already MERGED (the W2-acceptance hold is now clear). Only open L1 PR was #1766: rebased,
  regenerated the L1-only analysis pin (stale from this PR's own `ga_vargas_writer.py` change,
  per the new #1815 merge-group gate), dequeued/force-pushed/re-armed auto-merge. No E-gate
  dispatch this cycle — that is next cycle's priority-1 item once #1766's checks confirm queued.
  No new adjudication issue needed. `CYCLE 1 L1: fixed #1766's stale pin (dequeue+regen+re-arm) →
  next: verify #1766 is:queued, then act on the now-clear W2 acceptance-event hold / check E-gate`.
- 2026-09-05T13:53Z — **CYCLE 2 (C8 v2.3).** PR hygiene: #1766/#1827 both still BLOCKED (checks
  in flight, all green so far) — not RED/DIRTY, nothing to fix, left for next cycle to re-verify
  `is:queued`. Unit of work: proved the W2 acceptance-event mechanism end-to-end on the canary
  `ga_positions` — `asset_analysis_accepted` + `optimization_verdict_accepted` both HTTP 201 via
  the executor OIDC route; E-gate now reads `w2_analysis=t w2_verdict=t gate=OPEN-PENDING-PIN` for
  `ga_positions`, the first L1 asset to clear condition 2. No new adjudication issue needed.
  `CYCLE 2 L1: proved W2 acceptance-event mechanism on canary ga_positions (both events HTTP 201,
  E-gate cond 2 now open) → next: batch remaining 18 assets' W2 acceptance events, then claim a run
  slot and dispatch ga_positions W4`.
- 2026-09-05T14:00Z — **CYCLE 3 (C8 v2.3).** PR hygiene: `is:queued` shows #1766 now genuinely
  queued (checks finished green); #1827 still checks-running, all green, nothing RED/DIRTY.
  Unit of work: batched the remaining 10 `rebuild_only` L1 assets' W2 acceptance events (20 POSTs,
  all HTTP 201). E-gate now reads condition-2-clear for 11/19 L1 assets (`ga_positions` + all 10
  `rebuild_only`); the 8 `changed` assets are the only ones left needing acceptance events, held
  for their own cycle per D-L1-23 (higher-stakes verdict category; `ga_vargas` blocked on #1766
  deploying first). No new adjudication issue needed. `CYCLE 3 L1: batched 10 rebuild_only assets'
  W2 acceptance events (20/20 HTTP 201, E-gate cond 2 now clear for 11/19 L1 assets) → next: claim
  a run slot and dispatch ga_positions through W4 (the only asset with BOTH E-gate conditions open
  right now), or wait on #1766 merge to unlock the 8 changed assets' acceptance events`.
- 2026-09-05T14:09Z — **CYCLE 4 (C8 v2.3).** PR hygiene: #1766/#1827 both clean, nothing to fix.
  Unit of work: produced ga_positions' C13/D-NATIVE-05 blast-radius statement -- cascade closure
  is IN-LAYER only (chart_fact_identity, scoped-measured 530 rows, not the naive 270,471
  table-wide count), no-FK referrer (chart_facts_history) genuinely empty for this chart.
  Dispatch verdict: CLEAR, no adjudication needed. Did not also dispatch this cycle -- #1713 shows
  L3 and L5 both claimed slots in the last few minutes, 0-1 free; one bounded unit per cycle.
  CYCLE 4 L1: produced ga_positions blast-radius statement (IN-LAYER, 530 scoped rows, dispatch
  clear) -- next: re-check slot occupancy on #1713, claim a slot, dry-run then --commit
  --acknowledge-destroys the ga_positions W4 build with a fresh snapshot ref.
