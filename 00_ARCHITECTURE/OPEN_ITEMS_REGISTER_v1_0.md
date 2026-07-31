---
artifact: OPEN_ITEMS_REGISTER_v1_0.md
canonical_id: OPEN_ITEMS_REGISTER
version: 1.1
status: RECONCILED
created: 2026-06-17
reconciled: 2026-07-30
reconciled_by: SAMĀPTI lane B-OIR-RECONCILE (brief v2.0 §12.6 · OIR-INHERIT)
purpose: >
  Consolidated inventory of open items as of L0-sealed + L1-enrichment-sealed, BEFORE the L1 Gaṇita closure
  pass. Authored so nothing is silently absorbed or lost when the next big pass opens. Grouped by urgency
  relative to L1 closure; each item tagged owner (Cowork-plan / Claude-Code-exec / operator) + status.
  v1.1 adds the reconciliation pass this register was written to make possible: every never-closed item
  (A4, B2–B6, C2–C5, D3, D4, E3) probed against live code + live production DB and dispositioned. See §RECONCILIATION.
governing_decisions:
  - Gate-3 runs as its OWN pass BEFORE the L1 closure (native, 2026-06-17) — a layer can't close with assets unbuilt.
  - Connection-resilience guards = VERIFY before trusting (status unconfirmed; only the ga_sensitive heavy split is confirmed).
  - 2026-07-30 — the B2/B3/B4 ⚠️ VERIFY flags are DISCHARGED. All three guards are present and live; evidence in §RECONCILIATION.
changelog:
  - v1.1 (2026-07-30) — RECONCILIATION pass. 13 never-closed items dispositioned against probe evidence
    (5 ALREADY-FIXED, 3 OBSOLETE, 4 STILL-OPEN, 1 SUPERSEDED-BY-LANE). Per-item Status cells updated in place;
    new §RECONCILIATION section carries the probes, the commands, and 6 newly-surfaced residuals.
  - v1.0 (2026-06-17) — original register.
---

# Open Items Register v1.0 — what to close before / around the L1 Gaṇita closure

## Corrected sequence (native-ratified 2026-06-17)

1. **Six-subsystem Gate-3** (its own operator pass) — build the 4 per-chart subsystem L1 assets for the native.
2. **L1 Gaṇita closure pass** — on the now-fully-populated layer (kickoff already written).
3. **L2 Bodha design** — with closed L0 + closed L1 + accumulated opportunity register.
Cosmetic/CI items (group A) can run in parallel anytime; the L0/L1 residuals (group C) are tracked, non-blocking.

---

## GROUP A0 — Cockpit asset-state issues found via Chrome MCP 2026-06-17 (live localhost inspection)

Direct cockpit inspection of `/clients/482012f1/nirmana` surfaced 4 distinct classes. Most are metadata-hygiene
the L1 closure sweeps; TWO are genuinely-unbuilt Gate-3 data (confirming Gate-3 must run BEFORE L1 closure).

| # | Asset(s) | Symptom | Class | Fix path |
|---|---|---|---|---|
| A0-1 | L0 **bg_reference** (Reference Library, 1,485) + **bg_ontology** (Ontology, 623) | bare count, EMPTY bar, no `/target` | **NULL target_floor** → bar has no denominator to fill (display bug; data is LIVE/fine). These 2 had no floor at all so slipped the L0 floor-backfill | Set target_floor=achieved (1,485 / 623) + seed patch. Quick L0 touch-up (sealed L0 — log as L0 micro-fix, native already aware). |
| A0-2 | L1 **ga_str03 Graha-sthāna** (530/50) + **Saṃracanā/Structural** (87,169/74,644) | count > target (overfill) | **stale target_floor** | Bump floors to achieved count. → L1 closure Phase 2. |
| A0-3 | L1 **Sāḍesātī** (11,019), **Nakṣatra-Paṭala** (1,802, Last-Built "—"), **Vastu-graha-dik-mapa** (40), **Gochara Sthāna/transit-anchors** (45), **Saṃracanā** — ~5 assets | "build-state stale" badge; data present + counts match | **asset_throughput out of sync** — mostly SUBSYSTEM assets built/seeded outside the orchestrator throughput-write path (same class as L0's bg_transit_engine/bg_nakshatra_medical stale fix) | Re-sync throughput records. → L1 closure Phase 2 (and Gate-3 builds will refresh several). |
| A0-4 | L1 **ga_prashna** (Praśna-ādeśa, `0` NOT BUILT red) + **ga_yoga** (Yoga Firings, `5/50` partial red+stale) | red/partial in cockpit | **⚠️ CORRECTED 2026-06-17: NOT unbuilt — both are BUILT + CORRECT per `SIX_SUBSYSTEM_BUILD_CLOSE_v1_0.md` (Gate-3 already PASSED).** ga_prashna=0 is CORRECT (natal chart, no horary question → 0 rows, RT-7). ga_yoga=5 is CORRECT (only Yuga Nabhasa fires for this native — deterministic). The cockpit is MIS-RENDERING both. | (a) ga_prashna: cockpit DISPLAY BUG — treats 0-rows as NOT-BUILT when 0 is the valid built state for a natal prashna asset; cockpit needs a "0-rows-is-valid" signal (catalog_status/state vs rows). (b) ga_yoga: stale target_floor 50→5 + stale throughput. → L1 closure Phase 2 + a cockpit-render fix. **Supersedes the earlier "Gate-3 must precede L1 closure" claim — Gate-3 is DONE.** |

Note: L1 also confirmed the enrichment landed — Balatva/Strength 11,936 (4h ago), Sūkṣmabindu/Sensitive 8,610
(47m ago) both LIVE+fresh = PR #298 prod-validated in the cockpit.

## CLOSE-OUT STATUS 2026-06-18 (pre-L2 cleanup complete)

- L0 + L1 BOTH prod-sealed + verified (L0 PR #297 @ a6f564cc; L1 PR #299 @ 37ebd082; L1 prod-verify VERIFIED v2.1).
- Cockpit GENUINELY clean — endpoint-verified (camelCase-probe artifact resolved; bo_samskara count_sql fixed mig 314). [[feedback-verify-cockpit-endpoint-not-just-sql]]
- Migration ledger reconciled 311–314 (IDs 76–79).
- 11 stale open PRs audited → 10 CLOSED as superseded (#172/#180/#183/#185/#190/#194/#195/#196/#199/#206, each with documented reason); **#179 KEPT** (unmerged cascade-modal/route work — cherry-pick-or-close later).
- Brahma Conductor scheduled CI (red every 15min, obsolete autonomous-build path) → schedule removed, PR #300 OPEN (merge to stop the red; Cloud Scheduler watchdog already paused). Real gates (Gaṇita Quality Gate + Deploy to Cloud Run) GREEN.
- REMAINING (non-blocking): merge PR #300; decide #179 (cherry-pick cascade work or close); Group A4 (chore/repo-hygiene-isolated branch + /Madhav-nirmana-ui dir); Group C L0 residuals (DEFER-001..005, REC-003) tracked.
  - *(2026-07-30 reconciliation: A4 is ✅ ALREADY-FIXED; of the C residuals only DEFER-003, DEFER-004's `classical_chunks` half, and DEFER-005 remain — REC-003 and DEFER-004's `prashna_charts` half are ⛔ OBSOLETE. PR #300 / #179 were outside this pass's scope and are not dispositioned here. See §RECONCILIATION.)*
- **NEXT: L2 Bodha** — foundation clean. bo_samskara fix already cleared the first L2 schema issue.

## GROUP A — Cockpit / CI hygiene (parallel; do before or alongside L1 closure)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| A1 | **Cosmetic cockpit polish** — services-first ordering, service green-bar dimension match, centered headers, centered Last Built column | Claude-Code | Brief written, NOT run | `CLAUDECODE_BRIEF_COCKPIT_COSMETIC_v1_0.md`. Edits `AssetRow.tsx` — overlaps A2's red test. |
| A2 | **Main CI red** — `AssetRow_CockpitPolishR2.test.tsx` | Claude-Code | ✅ FIXED (commit 70c55e0c) | Stale `getByText('● GREEN')` → `getByTitle('CURRENT · healthy')` matching the StatusDot refactor (test was stale, not code). 4,526 tests 0 failures. Main CI trustworthy again. **A1 cosmetic brief must keep this green.** |
| A3 | **floor = count exact-match** — ga_strength/condition/sensitive have target_floor == achieved count; any future legit row change false-flags | Cowork-note | Logged, no action | Rail for L1 audit: "count BELOW floor" is the only alarm; "above" is fine; these 3 need a floor bump on future enrichment. |
| A4 | **`chore/repo-hygiene-isolated` branch SKIPPED** (unmerged commits) + **`/Madhav-nirmana-ui/` dir on disk** post-worktree-prune | Claude-Code | ✅ ALREADY-FIXED (reconciled 2026-07-30) | Branch absent from every ref. Its "unmerged" tip `31ed3d3d` is a rebase-duplicate of `44e89e10` — **identical patch-id `92f43a6c…`** — and `44e89e10` is on `origin/main` via merge `41000325`. Zero unique content. No `*nirmana*ui*` directory exists on disk. See §RECONCILIATION A4. |

## GROUP B — Connection resilience (from the 2026-06-17 orphaned-txn incident)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| B1 | **ga_sensitive light→heavy split** (5 per-ayanamsha substeps, independent commits) | Claude-Code | ✅ DONE (PR #298) | The durable crash-resilience fix; now a PATTERN for other multi-ayanamsha writers. |
| B2 | **idle_in_transaction_session_timeout guard** (DB backstop) — *Guard A* | Claude-Code | ✅ ALREADY-FIXED · VERIFY DISCHARGED (2026-07-30) | **Applied and live.** `pg_roles.rolconfig` for `amjis_app` = `{idle_in_transaction_session_timeout=600s, statement_timeout=1800s}`; live session reports `setting=600000, source=user`. Landed by `platform/supabase/migrations/241_idle_in_transaction_timeout.sql` (applied 2026-06-22). ⚠️ Residual R-1: migration says `120s`, production says `600s` — undocumented drift. |
| B3 | **finally/rollback guard in orchestrator txn path** (root-cause fix) — *Guard B* | Claude-Code | ✅ ALREADY-FIXED · VERIFY DISCHARGED (2026-07-30) | **Present and named in code.** `runner.py:813` `finally:` block is literally commented *"Guard B: roll back any open transaction BEFORE releasing the advisory lock"*; plus per-worker `finally: wconn.close()` (runner.py:517), per-substep `SAVEPOINT writer_exec` + `ROLLBACK TO SAVEPOINT` on exception (asset_runner.py:438-444), and a `SIGTERM` drain handler (runner.py:655). Landed in `e68206bf` / `95f40f12`. |
| B4 | **parallelism cap** (orchestrator worker concurrency vs 50-conn ceiling) | Claude-Code | ✅ ALREADY-FIXED · VERIFY DISCHARGED (2026-07-30) | **Cap set AND the budget written down.** `runner.py:67-79` states the invariant `_MAX_CONCURRENT_RUNS × (1 + _WORKER_LIMIT) ≤ ~33`; defaults 6 × (1+4) = 30 against a live `max_connections=50`. `_MAX_CONCURRENT_RUNS` is enforced (not just documented) at `runner.py:691`. |
| B5 | **PgBouncer pooler** (long-term connection fix) | operator/brahma-pipeline | 🔶 STILL-OPEN — correctly deferred (2026-07-30) | Not built: zero `pgbouncer`/pooler/`:6543` config in `infra/`, `.github/`, or platform config; the only 3 mentions in the repo are docs describing it as deferred. **The amplifier it targets is no longer binding**: live probe = 10/50 connections, 0 `idle in transaction`, worst-case orchestrator draw 30. Keep deferred; not a closure blocker. |
| B6 | **light→heavy audit for OTHER multi-ayanamsha L1 writers** | fold into L1 closure | 🔶 STILL-OPEN — narrowed (2026-07-30) | **The audit is now performed** (this pass): 14 of 19 `ga_*` orchestrator adapters declare `plan_substeps` (heavy). **5 remain light** — `ga_panchanga`, `ga_positions`, `ga_sade_sati`, `ga_strength`, `ga_tajaka` — and each underlying writer loops all 5 `CANONICAL_AYANAMSHAS` inside a single orchestrator-owned transaction (their `conn.commit()` is `owns_conn`-guarded, i.e. standalone-CLI only). Largest exposure: `ga_strength` @ 13,195 rows/chart, `ga_sade_sati` @ ~6,280. Same class as the ga_sensitive fix. |

## GROUP C — L0 residuals (disclosed at L0 seal; tracked, NON-blocking for L1)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| C1 | **DEFER-001/002** — bg_transit_engine + bg_nakshatra_medical have NO WriterBase writer (data migration-seeded, not orchestrator-reproducible) | Claude-Code | ✅ RESOLVED (Foundation-Session-1 2026-06-18) | bg_transit_rules writer added (folds bg_transit_engine); bg_medical_mappings writer already registered bg_nakshatra_medical. Both confirmed regenerable. |
| C2 | **DEFER-003** — reference_nakshatras DROP needs bg_reference.py refactor first (still INSERTs into it) | Claude-Code | 🔶 STILL-OPEN — blocker cleared, DROP not done (2026-07-30) | **The refactor half is DONE**: `l0_reference.py:1336` now reads `if False:  # superseded by bg_nakshatra writer` — the INSERT is dead code (commit `1efa18dd`). Table still exists (27 rows) with the mig-302 deprecation comment. Remaining: delete the dead block, retarget 2 test files that still assert on it (`test_bg_reference.py`, `test_bg_dignity_reference.py`), then the DROP migration. ⚠️ Residual R-3: the live table comment still claims "kept alive only because bg_reference writer still inserts into it" — now false. |
| C3 | **DEFER-004** — classical_chunks + prashna_charts (empty) DROP needs code-ref removal first | Claude-Code | **SPLIT** (2026-07-30) — `prashna_charts` ⛔ OBSOLETE · `classical_chunks` 🔶 STILL-OPEN | **`prashna_charts` is no longer a drop candidate**: it holds 2 rows and is actively INSERTed by `ga_prashna_cast.py:170`. Premise falsified — remove from the drop list. **`classical_chunks`**: still 0 rows; the *named* blocker is cleared (`l0_text_index.py::_search_classical_chunks` queries `classical_text_chunks`, not this table — only the function *name* is legacy) but ~8 other live surfaces still reference it (`platform/tests/classical/classical_texts_smoke.test.ts`, `platform/scripts/verify_classical_texts_data.ts`, `scripts/m9/*.py`, `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/*`). ⚠️ Residual R-4: two stale table comments (mig 303). |
| C4 | **DEFER-005** — bg_nakshatra upstream-hash tracking broken (hashes empty string; latent silent-staleness) | Claude-Code | 🔴 STILL-OPEN — confirmed live, and BROADER than recorded (2026-07-30) | **Reproduced.** `compute_upstream_hash` (asset_runner.py:114) hashes the `depends_on` fan-in; for a dependency-free asset the payload is `''` → the constant `sha256('')[:16] = e3b0c44298fc1c14`, which can never change. Live: **15 `asset_throughput` rows across 11 root assets** carry that constant (`bg_class_priors`, `bg_formula_constants`, `bg_ghatana`, `bg_medical_mappings`, `bg_prashna_rules`, `bg_transit_rules`, `bg_vastu_directions`, `bg_vidhi_primitives`, `ga_positions` ×3, `ka_gochara_resonance` ×3, `mi_vistara`); 21 more are NULL, `bg_nakshatra` among them. Change-detection is a permanent no-op for every root asset — not just bg_nakshatra. File as a tracked issue. |
| C5 | **REC-003** — brahma_dosha_catalog.associated_remedies[] empty for all 50 doshas | data task | ⛔ OBSOLETE as a gate — field genuinely unused (2026-07-30) | **The stated dependency is falsified.** As-built `bo_upaya` reads `brahma_remedy_corpus` (266 rows), never `brahma_dosha_catalog.associated_remedies` — grep of the whole repo finds the column only in `l0_doshas.py` (seeded `[]` with the comment *"Tier 3 fills"*) and mig 176's DDL. L2 shipped without it: `bodha_rm_remedy_prescriptions` = 405 rows, `bodha_rm_dosha_remedy_bundles` = 5. Field is still 79/79 empty (catalog grew 50→79) but nothing consumes it. Re-scope as an optional enrichment, not a pre-L2 gate. |

## GROUP D — Larger parallel workstreams (standing, from memory)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| D1 | **Six-subsystem Gate-3** — per-chart L1 subsystem data for 482012f1 | operator | ✅ DONE + SEALED 2026-06-17 (`SIX_SUBSYSTEM_BUILD_CLOSE_v1_0.md`) | All 8 assets lit (ga_yoga 5, ga_prashna 0-correct, ga_structural 75,168, ga_condition 45, ga_transit_anchors 45, ga_vastu 40, ga_medical 45, ga_sade_sati 11,019 = 86,367 rows). FORENSIC 7/7, Vimarśaka RT clean. **No longer gates L1 closure — it's complete.** Sealed on branch feature/bg-nakshatra-l0 (verify merged to main). |
| D2 | **227-file brief purge** | Claude-Code | ✅ DONE (PR #282 @ d9c668ca) | 229 non-CURRENT briefs → 99_ARCHIVE/BRIEFS_RETIRED/ (290 total archived); 5 CURRENT/ACTIVE/READY retained by STATUS not count (reverse-citation discipline held). G52 signal_type_registry also eliminated (PR #281, 0 live refs). 85 live briefs remain. |
| D3 | **Tier-3 merge queue + Tier-B branch audit** — accumulated worktrees/branches awaiting reviewed merges | Claude-Code | 🔶 STILL-OPEN → **SUPERSEDED-BY-LANE** (2026-07-30) | Measured, and materially worse than at authoring: **168 remote branches not merged into `origin/main`** (41 merged, 207 heads total), 335 local branches, **70 worktrees**. The "~per-branch sessions; never batch" prescription does not scale to 168. Ownership transfers to SAMĀPTI lanes **C7-WORKTREE-RETIRE** (worktrees) and **E1-SAMGATI §8.1–8.3** (uncommitted / unpushed / dangling-PR sweep). Do not re-open here. |
| D4 | **feature/panchanga-service-registry branch** — pending its own PR (independent of layer closures) | Claude-Code | ✅ ALREADY-FIXED (2026-07-30) | Branch absent from every local ref, remote ref, and tag (`git for-each-ref` + `git ls-remote origin`). The feature it named is merged on `origin/main`: `7f65d19f feat(panchanga): service registry + cockpit v2 service-health rendering (#246)` (2026-06-11), confirmed ancestor of `origin/main`. Nothing pending. |

## GROUP E — Foundation-Session-1 residuals (2026-06-18, pre-L2)

| # | Item | Owner | Status | Note |
|---|---|---|---|---|
| E1 | **bg_remedies depth / bo_upaya dependency** — bg_remedies has 266 rows (first deterministically-citable pass; classical tradition has thousands). L2 bo_upaya (remedy prescription layer) will read bg_remedies depth directly. | Cowork-plan | LOGGED, DEFERRED to L2 | Accept 266 as-built. A future bg_remedies expansion pass is needed BEFORE bo_upaya produces rich outputs. Flag at bo_upaya spec time. |
| E2 | **bg_rules yield = corpus ceiling** — full 10,651-chunk mine confirmed 2,912 rules (0 new insertions); remaining 9,625 chunks don't contain regex-extractable rule patterns. The current regex pattern library (19 patterns) is the yield ceiling for the existing corpus. | Cowork-note | LOGGED, no action | Expanding yield requires either (a) new pattern families or (b) corpus expansion (more classical_text_chunks). Floor = 2,912 (ACHIEVED). |
| E3 | **bg_yogas count 175 in DB vs 144 in l0_yogas.py** — endpoint shows bg_yogas=175 (in brahma_yoga_catalog); YOGAS_CORE=144. Discrepancy: the DB may contain the full 175-entry catalog including entries beyond YOGAS_CORE. Verify if intentional or a stale count. | Claude-Code | ⛔ OBSOLETE — question ANSWERED, hypothesis REFUTED (2026-07-30) | **The 175 was never `brahma_yoga_catalog`.** Live: catalog = **186**; `reference_yogas` = **175**; `brahma_ontology(entity_class='yoga')` = **175**; `asset_throughput.rows_written` = **175**. The endpoint's 175 is the pointer/ontology population, not the catalog. **144 ≠ 175 is by design**: `l0_yogas.py` seeds `YOGAS_CORE` (144, asserted by `test_ga_yoga.py:72`) *plus* `extract_yogas_from_corpus()` (l0_yogas.py:1843, regex mining of `classical_text_chunks`). So "YOGAS_CORE may be incomplete" is **refuted** as the explanation. Two real residuals surfaced instead — R-5, R-6 below. |

---

## What gates what (the dependency the native cares about)

- **L2 Bodha is gated behind:** Gate-3 (D1) populating the subsystem data + the L1 closure sealing the layer +
  REC-003 (C5) data. Bodha reading empty subsystem inputs = building MSR signals on nothing.
- **L1 closure is gated behind:** Gate-3 (D1) — can't close a layer whose subsystem assets aren't built for the native.
- **Nothing critical gates the cosmetic/CI items (A)** — but A2 (CI green) should precede the multi-PR L1 closure so the merge signal is trustworthy.

*End of v1.0 body. Original recommended order: (1) verify B2–B4 + run A1/A2 to green CI; (2) Gate-3 (D1); (3) L1 closure pass
(folding B6 audit + C-residuals awareness); (4) L2 Bodha. C/D residuals tracked throughout, closed opportunistically.*

---

# RECONCILIATION — 2026-07-30

**Lane:** SAMĀPTI `B-OIR-RECONCILE` · brief `SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md` §12.6 (OIR-INHERIT).
**Baseline:** `origin/main` @ `5f5033a5`. **DB:** production, PostgreSQL 15.17.
**Standard:** no item may be dispositioned "presumed obsolete." Every disposition below is backed by a
grep over the source tree, a query against the live production database, or a git-object proof.

## Disposition summary

| Disposition | Count | Items |
|---|---|---|
| ✅ **ALREADY-FIXED** | 5 | A4, B2, B3, B4, D4 |
| ⛔ **OBSOLETE** (premise falsified / question answered) | 3 | C3 *(prashna_charts half)*, C5, E3 |
| 🔶🔴 **STILL-OPEN** | 5 | B5, B6, C2, C3 *(classical_chunks half)*, C4 |
| ➡️ **SUPERSEDED-BY-LANE** | 1 | D3 → C7-WORKTREE-RETIRE + E1-SAMGATI |

*(13 distinct register items — A4, B2, B3, B4, B5, B6, C2, C3, C4, C5, D3, D4, E3. C3 splits across two
rows, so the column sums to 14.)*

**Headline:** the three ⚠️ VERIFY flags this register was authored to force — **B2, B3, B4 — are all
DISCHARGED**. All three connection-resilience guards from the 2026-06-17 orphaned-txn incident were in
fact implemented; nobody had ever gone back to confirm it. The live DB now shows 10/50 connections and
**zero** `idle in transaction` sessions, which is the incident's own success criterion, met.

## Per-item evidence

### A4 — `chore/repo-hygiene-isolated` + `/Madhav-nirmana-ui/` → ✅ ALREADY-FIXED

The branch exists in no ref of any kind:

```
git for-each-ref --format='%(refname)' | grep -i hygiene   → only unrelated wave/D-4b + docs/rc15 refs
git ls-remote origin | grep -Ei "hygiene|nirmana"          → 2 unrelated heads, no repo-hygiene-isolated
```

Its recorded "unmerged commits" are a **rebase-duplicate of already-merged content**. Reflog (shared
checkout) shows the branch was rebased to tip `31ed3d3d` from `44e89e10`. Patch-id proof:

```
git show 44e89e10 | git patch-id --stable  → 92f43a6c3a9845c9f2114d32dc77d2a30ed0ab48
git show 31ed3d3d | git patch-id --stable  → 92f43a6c3a9845c9f2114d32dc77d2a30ed0ab48   ← identical
git merge-base --is-ancestor 44e89e10 origin/main → true (merged via 41000325, 2026-06-16)
```

`31ed3d3d` is not an ancestor of `origin/main`, but it introduces **zero** content that `44e89e10` did
not already land. Nothing to recover.

Directory: `find /Users/Dev/Vibe-Coding/Apps -maxdepth 4 -iname "*nirmana*ui*"` → no directory match
(only unrelated `NIRMANA_*.md` docs and `nirmana-*.png` screenshots). Already removed.

### B2 — Guard A · `idle_in_transaction_session_timeout` → ✅ ALREADY-FIXED (VERIFY discharged)

```sql
SELECT rolname, rolconfig FROM pg_roles WHERE rolconfig IS NOT NULL;
→ amjis_app | {idle_in_transaction_session_timeout=600s, statement_timeout=1800s}

SELECT name, setting, source FROM pg_settings WHERE name='idle_in_transaction_session_timeout';
→ idle_in_transaction_session_timeout | 600000 | user
```

Source: `platform/supabase/migrations/241_idle_in_transaction_timeout.sql`, applied 2026-06-22
(`_migrations_applied`). The migration header names it *"Guard A"* and cites the Jun-17 incident by name.

Nuance worth recording: `pipeline/orchestrator/db.py:31,45` deliberately sets the timeout to `0` on
build-worker connections (both via libpq `options` and an explicit `SET`, defence-in-depth against a
proxy stripping the startup option), because a writer legitimately holds a transaction open through
minutes of pure CPU work. The guard therefore protects every *other* client of the build role while the
orchestrator opts out on purpose — and Guard B (below) is what covers the orchestrator's own path.

### B3 — Guard B · finally/rollback in the orchestrator txn path → ✅ ALREADY-FIXED (VERIFY discharged)

The guard is present *and named*, in `pipeline/orchestrator/runner.py:813`:

```python
finally:
    # Guard B: roll back any open transaction BEFORE releasing the advisory
    # lock, so a killed/interrupted build never leaves a txn open on the
    # connection. Advisory locks are session-level and survive ROLLBACK, so
    # the unlock below is still effective after the rollback.
```

Supporting layers, all confirmed by read:
- per-worker `finally: wconn.close()` — `runner.py:517`
- per-substep `SAVEPOINT writer_exec` → `ROLLBACK TO SAVEPOINT` on any exception, re-raised —
  `asset_runner.py:438-444`
- `SIGTERM` handler installed for graceful drain — `runner.py:655`, flag checked each scheduler round
  (`runner.py:290`)

Provenance: `e68206bf fix(ga_sensitive): convert to heavy writer; add runner conn-resilience` and
`95f40f12 fix(l1-closure): Phase 2 integrity fixes — floors, bare excepts, Guard B, migration 308`.

### B4 — parallelism cap vs the 50-connection ceiling → ✅ ALREADY-FIXED (VERIFY discharged)

`pipeline/orchestrator/runner.py:67-79` carries the budget as a stated invariant, not folklore:

```
# ── Connection budget (Cloud SQL max_connections=50; ~33 available to orchestrator) ──
#     _MAX_CONCURRENT_RUNS × (1 + _WORKER_LIMIT) ≤ ~33
# Defaults: 6 × (1 + 4) = 30.
_MAX_CONCURRENT_RUNS = int(os.environ.get("ORCHESTRATOR_MAX_CONCURRENT_RUNS", "6"))
_WORKER_LIMIT        = max(1, int(os.environ.get("ORCHESTRATOR_WORKER_LIMIT", "4")))
```

Enforced, not merely documented: `runner.py:691` refuses a new run when `active_count >=
_MAX_CONCURRENT_RUNS`. `_WORKER_LIMIT` bounds the `_DaemonThreadPoolExecutor` at `runner.py:287`.
Live ceiling confirmed: `SELECT setting FROM pg_settings WHERE name='max_connections'` → `50`
(source: configuration file). So the register's open question — "was the cap set, or did only the heavy
split mitigate it?" — resolves to: **the cap was set, and the arithmetic is written down.**

### B5 — PgBouncer pooler → 🔶 STILL-OPEN, correctly deferred

Not implemented. `grep -rilE "pgbouncer|pooler|:6543" infra/ .github/ platform/*.json` → no hits. The
only three occurrences in the repo are prose describing it as future work
(`PRE_L2_TAKE_STOCK_v1_0.md`, `PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md`, and this register).

But the urgency is gone. Live probe:

```sql
SELECT count(*) FROM pg_stat_activity                                → 10
SELECT count(*) FROM pg_stat_activity WHERE state='idle in transaction' → 0
```

10 of 50 connections in use, zero orphaned transactions, worst-case orchestrator draw 30. B5 stays a
brahma-pipeline backlog item; it is not a closure blocker and should not be escalated on incident
grounds that no longer hold.

### B6 — light→heavy audit of the other multi-ayanamsha L1 writers → 🔶 STILL-OPEN, narrowed

The audit the register asked for had never been run. Running it now:

```
for f in pipeline/orchestrator/writers/ga_*.py; do grep -c "def plan_substeps" $f; done
```

| Heavy (`plan_substeps` declared) — 14 | Light (`run()` only) — 5 |
|---|---|
| ga_ayurdaya, ga_condition, ga_dashas, ga_medical, ga_nakshatra, ga_prashna, ga_sensitive, ga_sensitive_degree, ga_structural, ga_transit_anchors, ga_vargas, ga_vastu, ga_vichara, ga_yoga | **ga_panchanga, ga_positions, ga_sade_sati, ga_strength, ga_tajaka** |

All five light writers loop the full `CANONICAL_AYANAMSHAS` set inside one orchestrator-owned
transaction — verified by reading each: e.g. `ga_positions_writer.py:603` iterates all 5 ayanamshas and
its only `conn.commit()` (line 640) is guarded by `if owns_conn:`, i.e. it fires solely on the standalone
CLI path. Same shape in `ga_strength_writer.py` (loop 1693, `if owns_conn: conn.commit()` 1822-1823),
`ga_panchanga_writer.py` (loop 1425, commit 1449 — and it accumulates every ayanamsha's rows into one
`_insert_chart_facts_rows` call after the loop), `ga_tajaka_writer.py` (loop 743, commit 792), and
`ga_sade_sati_writer.py` (loop 1871). Under the orchestrator all five commit **once, at the end** —
precisely the exposure `ga_sensitive` was split to remove.

Sizing (production `asset_throughput`, per chart): `ga_strength` 13,195 · `ga_sade_sati` ~6,280 ·
`ga_positions` 1,205 · `ga_panchanga` ~430 · `ga_tajaka` ~260. `ga_strength` and `ga_sade_sati` are the
two worth converting.

### C2 — DEFER-003 · `reference_nakshatras` → 🔶 STILL-OPEN, blocker cleared

The blocker migration 302 recorded ("kept alive only because bg_reference writer still inserts into it")
**no longer exists**. `platform/python-sidecar/brahmagyan/l0_reference.py:1336`:

```python
        # -- reference_nakshatras --
        if False:  # superseded by bg_nakshatra writer
            inserted = 0
            for nak in NAKSHATRAS:
                cur.execute(""" INSERT INTO reference_nakshatras ... """)
```

Landed by `1efa18dd feat(bg_reference): stop seeding reference_nakshatras — superseded by bg_nakshatra
writer`. Table still present with 27 rows. What actually remains before the DROP:
1. delete the dead `if False:` block;
2. retarget two live tests that still assert against the table —
   `writers/tests/test_bg_reference.py:35,44,57,72` (floor ≥ 27) and
   `writers/tests/test_bg_dignity_reference.py:186-228` (cross-checks its `lord` / degrees against the
   canonical `reference_nakshatra`);
3. the DROP migration.

### C3 — DEFER-004 · `classical_chunks` + `prashna_charts` → SPLIT

**`prashna_charts` → ⛔ OBSOLETE.** No longer empty and no longer a drop candidate:
`SELECT count(*) FROM prashna_charts` → **2**, and `ga_writers/ga_prashna_cast.py:170` INSERTs into it.
It is a live table. Remove it from the residual-drop list entirely.

**`classical_chunks` → 🔶 STILL-OPEN.** `SELECT count(*)` → **0**. The specific blocker migration 303
named is gone: `l0_text_index.py::_search_classical_chunks` (line 235) queries `classical_text_chunks`
(lines 268, 287) — only the *function name* is legacy. But a strict `\bclassical_chunks\b` grep still
finds live references in `platform/tests/classical/classical_texts_smoke.test.ts` (asserts ≥ 4,000 rows
against a table that has 0), `platform/scripts/verify_classical_texts_data.ts`, `scripts/m9/*.py`,
`scripts/governance/v13_production_gate.py`, and `08_CLASSICAL_CROSS_REFERENCE/corpus/ingestion/*`. The
DROP is still blocked, by different code than recorded.

### C4 — DEFER-005 · broken upstream-hash change detection → 🔴 STILL-OPEN, broader than recorded

Root cause read from `pipeline/orchestrator/asset_runner.py:114`: `compute_upstream_hash` builds its
payload by joining the asset's `depends_on` fan-in. For an asset with `depends_on = '{}'` the query
returns no rows, the payload is the empty string, and the stored hash is the **constant**
`sha256('')[:16] = e3b0c44298fc1c14` — which by construction can never change, so
`staleness.ts`'s `up.content_hash !== asset.built_against_upstream_hash` comparison can never fire.

```sql
SELECT count(*) FILTER (WHERE built_against_upstream_hash='e3b0c44298fc1c14') AS empty_sha,
       count(*) FILTER (WHERE built_against_upstream_hash IS NULL)            AS null_hash,
       count(*) AS total
FROM asset_throughput;
→ empty_sha=15 | null_hash=21 | total=233
```

The 15 span 11 distinct dependency-free assets: `bg_class_priors`, `bg_formula_constants`, `bg_ghatana`,
`bg_medical_mappings`, `bg_prashna_rules`, `bg_transit_rules`, `bg_vastu_directions`,
`bg_vidhi_primitives`, `ga_positions` (×3 charts), `ka_gochara_resonance` (×3 charts), `mi_vistara`.
`bg_nakshatra` itself is in the NULL set (`depends_on = '{}'`, hash NULL, lit 2026-06-18).

So DEFER-005 is real, still present, and **is not a bg_nakshatra-specific defect** — it is a silent
change-detection hole across every root asset in the DAG. Data remains correct; staleness signalling
does not. Worth a tracked issue in its own right.

### C5 — REC-003 · `brahma_dosha_catalog.associated_remedies[]` → ⛔ OBSOLETE as a gate

The field is still empty — and now demonstrably unused:

```sql
SELECT count(*) AS doshas,
       count(*) FILTER (WHERE associated_remedies IS NULL OR cardinality(associated_remedies)=0) AS empty
FROM brahma_dosha_catalog;
→ doshas=79 | empty=79        (catalog grew 50 → 79 since authoring)
```

The register's gating claim was "Required pre-L2-Bodha (bo_upaya consumes it)." **The as-built writer
does not.** `pipeline/orchestrator/writers/bo_upaya.py` header: *"Reads bodha_msr_signals + L1
chart_facts + brahma_remedy_corpus"*; its remedy fetch is `SELECT ... FROM brahma_remedy_corpus`
(line 985) and its citations are `brahma_remedy_corpus/{remedy_id}` (line 1369). A whole-repo grep for
`associated_remedies` finds it **only** in `l0_doshas.py:1971` (seeded `[]`, comment *"Tier 3 fills"*)
and mig 176's DDL — no reader anywhere.

L2 shipped without it: `brahma_remedy_corpus` = 266 rows, `bodha_rm_remedy_prescriptions` = 405,
`bodha_rm_dosha_remedy_bundles` = 5. Re-scope REC-003 as optional catalog enrichment. (Note it interacts
with **E1** in this register — the standing `bg_remedies` depth item at 266 rows — which remains the real
remedy-depth question.)

### D3 — Tier-3 merge queue + branch audit → ➡️ SUPERSEDED-BY-LANE

```
git branch -r --no-merged origin/main | grep -v HEAD | wc -l   → 168
git branch -r --merged    origin/main | grep -v HEAD | wc -l   →  41
git branch --list | wc -l                                      → 335
git worktree list | wc -l                                      →  70
```

Materially worse than at authoring, and the v1.0 prescription ("~per-branch sessions; never batch") does
not scale to 168 branches. Ownership moves to the lanes already chartered for exactly this work:
**C7-WORKTREE-RETIRE** (worktree retirement, gated on `all_build_lanes_terminal`) and **E1-SAMGATI
§8.1–8.3** (uncommitted / unpushed / dangling-PR sweep across every wrapped arc). Tracked there, not here.

### D4 — `feature/panchanga-service-registry` → ✅ ALREADY-FIXED

Branch absent from every local ref, remote-tracking ref, tag, and from `git ls-remote origin` (the only
`panchanga` ref on the remote is the unrelated `fix/chart-facts-panchanga-category-alias`). The feature
it named is on `origin/main`:

```
7f65d19f feat(panchanga): service registry + cockpit v2 service-health rendering (#246)   2026-06-11
git merge-base --is-ancestor 7f65d19f origin/main → true
```

The register logged it as pending on 2026-06-17, six days after #246 merged. Nothing outstanding.

### E3 — bg_yogas 175 vs YOGAS_CORE 144 → ⛔ OBSOLETE (answered; hypothesis refuted)

Four counts, taken live:

| Surface | Count |
|---|---|
| `brahma_yoga_catalog` | **186** |
| `reference_yogas` | **175** |
| `brahma_ontology WHERE entity_class='yoga'` | **175** |
| `asset_throughput.rows_written` for `bg_yogas` | **175** |
| `YOGAS_CORE` in `l0_yogas.py` (imported and counted) | **144** |

So the endpoint's "175" was never the catalog — it is the pointer/ontology population, which is exactly
175 in three places at once. And 144 ≠ 175 is **by design**, not staleness: `l0_yogas.py` runs
`seed_yogas()` over the 144-entry inline `YOGAS_CORE` (asserted `== 144` by
`writers/__tests__/test_ga_yoga.py:72`) **and** `extract_yogas_from_corpus()` (line 1843), a regex miner
over `classical_text_chunks`. The register's hypothesis — *"if 175, YOGAS_CORE list may be incomplete"* —
is **refuted**: the extra rows are corpus-derived, not missing core entries. E3 as posed is closed.

The probe did, however, surface two genuine defects behind it — logged as R-5 and R-6 below.

## Residuals surfaced by this pass (discovered, not fixed — out of lane)

| # | Residual | Evidence | Suggested owner |
|---|---|---|---|
| **R-1** | **Guard A value drift, unrecorded.** Migration 241 sets `idle_in_transaction_session_timeout='120s'`; production has `600s`. No migration anywhere performs the change (`grep -rn "ALTER ROLE amjis_app"` → only mig 241). `db.py:37` documents `600s` as the role default, so the change was intentional but applied out-of-band. | `pg_roles.rolconfig` vs `241_idle_in_transaction_timeout.sql:15` | brahma-pipeline / governance |
| **R-2** | **B6 exposure quantified** — 5 L1 writers still commit a 5-ayanamsha loop as one transaction. See B6 above. | reader of `plan_substeps` census | L1 hardening |
| **R-3** | **Stale table comment** on `reference_nakshatras`: *"Kept alive only because bg_reference writer still inserts into it"* — false since `1efa18dd`. | `obj_description` vs `l0_reference.py:1336` | fold into the C2 DROP migration |
| **R-4** | **Two stale table comments** from mig 303: `classical_chunks` blames `l0_text_index.py` (which no longer touches it); `prashna_charts` says *"prashna charts not yet built in production"* while holding 2 rows. | `obj_description` on both tables vs live counts | fold into the C3 work |
| **R-5** | **47 of the 144 `YOGAS_CORE` canonical_ids have no row in `brahma_yoga_catalog`** — e.g. `kala_sarpa_yoga`, `raja_yoga_1_4/1_5/4_5/4_9/5_10`, `mahabhagya_female`, `nipuna_yoga`, the `jaimini_a*` set. `YOGAS_CORE` was last expanded 2026-06-18 (`6f4a007e`); catalog `created_at` buckets are 06-08 (86), 06-09 (89), 07-14 (4), 07-23 (7) — **nothing on the 2026-06-24 `last_built_at`**. The catalog has not been rebuilt against the current core list. | set-difference of `YOGAS_CORE` ids against `SELECT canonical_id FROM brahma_yoga_catalog` | L0 / bg_yogas rebuild |
| **R-6** | **OCR noise in a canonical catalog.** `extract_yogas_from_corpus()` derives `canonical_id` via `_snake(name)` off raw chunk text, admitting non-yoga tokens — live rows include `another`, `each`, `particular`, and OCR corruptions `dariclra`, `datidra`, `sankbe`, `rajiu`, `kimadruma`, `kemidruma`, `dhenub`, `rasiskedara`. 89 of the 186 catalog rows are outside `YOGAS_CORE`. | `SELECT canonical_id FROM brahma_yoga_catalog` | L0 / bg_yogas quality gate |
| **R-7** | **`bg_yogas` floor never reset to achieved** (§N.4 floors-are-aspirational): `asset_registry.target_floor = 250` while `count_sql` returns **536** and the catalog holds 186. Same class as the A0-2 stale-floor finding this register already recorded. | `asset_registry` + running its own `count_sql` | cockpit / floor sweep |

*End of RECONCILIATION 2026-07-30. Register status CURRENT → RECONCILED. What this register still carries
forward is exactly: the STILL-OPEN set (B5, B6, C2, C3-`classical_chunks`, C4), the seven residuals R-1…R-7
above, and D3's handoff to C7-WORKTREE-RETIRE / E1-SAMGATI. Everything else is closed with evidence.*
