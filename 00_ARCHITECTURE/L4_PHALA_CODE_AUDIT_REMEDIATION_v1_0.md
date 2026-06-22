---
artifact: L4_PHALA_CODE_AUDIT_REMEDIATION_v1_0.md
canonical_id: L4_PHALA_CODE_AUDIT_REMEDIATION
version: 1.0
status: CURRENT — code-grounded audit of the L4 build (worktree ground truth); supersedes the GitHub-based PR #328 review for findings
authored_by: Cowork 2026-06-22
audit_target: feature/l4-phala-autonomous @ cf4089f4 (live Antigravity worktree MadhavL4Phala)
audit_method: static read + grep + sqlglot parse-validation + pytest unit run + pkgutil import test (NO full data build)
supersedes_findings_in: L4_PHALA_PR328_REVIEW_v1_0.md (which was GitHub-files-API-based and partially wrong)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The authoritative gap list for the L4 Phala build, derived from the ACTUAL code in the Antigravity
  worktree (not GitHub, not the swarm self-report). Each gap carries severity, exact file, exact fix,
  and owner (swarm-autonomous vs native-decision). Drives the remediation pass before merge/seal.
---

# L4 Phala — Code Audit & Remediation Plan v1.0

> **Why this supersedes the PR #328 review.** That review read the GitHub `pull_request/files` API,
> which truncates large PRs at ~33 files. It produced two wrong calls — "337 is a stub → runtime
> crash" (the real `337_phala_phaladesa.sql` exists) and "rectification descoped" (the rectification
> stubs exist as dead files, not a clean descope). This audit read the real worktree. Trust this one.

## §0 — Audit method (ground truth)
- **Target:** the live worktree `…/.claude/worktrees/MadhavL4Phala` at `cf4089f4` = PR #328 head.
- **Note:** `git` cannot run in-sandbox (the worktree `.git` pointer references a macOS host path), so
  diff was done by direct content comparison against the `main` mount. Files read directly throughout.
- **Done:** every migration parse-validated (sqlglot, postgres dialect); every ph_* writer read +
  contract-checked; all 8 writers import-tested (pkgutil); 281 ph_/U-enabler unit tests run; registry,
  manifest, Dockerfile, deploy.yml inspected. **Not done:** a full orchestrator data-gen run (static+dry-run depth, per scope).

## §1 — What is GENUINELY SOLID (verified, not self-reported)
| Area | Finding |
|---|---|
| **Writer contract** | All 8 ph_* writers: correct `@register`, `WriterBase` subclass, `run(ctx)`, `WriterResult(rows_inserted=)`, **zero** `commit`/`close` violations, **zero** `asset_throughput` writes, delete-then-insert idempotency present. Fully frozen-contract-conformant. |
| **Anti-drift** | Zero out-of-layer writes. The only `UPDATE SET`s are `ON CONFLICT … DO UPDATE` upserts on the writers' OWN `phala_*` tables. Clean. |
| **Writer↔table alignment** | Every writer's target table exists in a real migration. `ph_phaladesa` writes `phala_phaladesa` (created by 337_phala_phaladesa.sql), **NOT** the dead `phala_outlook` stub. **No missing-table runtime crash.** |
| **Import sanity** | All 8 writers import cleanly via pkgutil — auto-discovery will not hard-fail the orchestrator at boot. Only third-party dep is `psycopg2` (present in the sidecar image). |
| **Model policy** | Anthropic ban is not just respected — it's **enforced in code**: `ph_phaladesa` has `validate_narration_model()` that raises `NarrationModelError` on any `claude-`/`anthropic/` model. |
| **U4 chart-generality** | **De-hardcoded correctly.** `school_runner.ts` takes `chartData` as a param and passes it to `engine.analyze(chartData,…)`; `chart_data_adapter.ts::buildChartData` builds from `chart_facts`. `ABHISEK_CHART` is defined once in `types.ts` as a fixture and is NOT referenced by any engine. (My earlier "engines still hardcoded" flag was a substring-grep artifact — cleared.) |
| **Migrations apply** | All 14 files apply cleanly. `migrate.ts` keys on **filename** (not number) + lexical order, so duplicate numbers do NOT collide; the empty stubs apply as no-op comments. All real DDL parse-validates. |
| **Hard gates in schema** | Leakage-firewall (`auto_action` CHECK = stage_for_review), no-scoring (`D5ViolationError`, no calibration column), cascade-depth ≤3 CHECK, `is_timing_refinement_signal` GENERATED column — all enforced in DDL, not just spec. |
| **CI infra** | `deploy.yml` PR-build-check builds BOTH images without push, **explicitly verifies `ga_writers` is importable in the pipeline image** (the import-hang guard), and runs `migrate.ts`. The infra to catch our failure modes exists. |
| **Test coverage** | Per-wave suites all present (`test_ph_wave4/5/6/7`, `test_ph_nimitta_spine`, `test_u1_dasha_consensus`, `test_u3_convergence_currents`, `test_phala_*`). 280/281 sampled pass. |

## §2 — GAPS (severity-ranked, code-grounded)

### 🔴 BLOCKER-1 — U2 (lifetime score enrichment) is UNBUILT
- **Evidence:** No U2 writer, no U2 service, no `lifetime`/`prana` source file anywhere on the branch.
  Migration `338_kala_convergence_horizon_tier.sql` is an empty PLACEHOLDER stub. `kala_jivana_parva`
  still has `avg_effective_score = NULL` throughout (739 rows) — the brief's exact AC (line 109 of
  `CLAUDECODE_BRIEF_U2_LIFETIME_PRANA_v1_0`) is unmet.
- **Impact:** The lifetime-horizon prediction tier has no scored substrate. ph_* assets use
  `phala_anchors.horizon_tier` (their own near/lifetime column) but the upstream L3 lifetime enrichment
  that was meant to feed it does not exist. Partial-supreme, not supreme.
- **Owner:** SWARM (autonomous). **Fix:** implement the U2 writer per the brief — score the 739
  `kala_jivana_parva` parvas (non-null `avg_effective_score`), add the real `kala_convergence.horizon_tier`
  DDL into 338, re-run, `[verify: prod]` non-null. Prāṇa stays dropped (D29 — no level-5, no new table).

### 🟠 MAJOR-2 — U3 per-current breakdown column UNBUILT (decide: build or descope)
- **Evidence:** `339_kala_convergence_current_breakdown.sql` is an empty stub; nothing reads a
  per-current breakdown column. The U3 *currents enrichment* logic (eclipse/t2t/station) DOES exist
  (`test_u3_convergence_currents.py` passes), but the optional §3.5 per-current **persistence column**
  was not written.
- **Impact:** Low if the currents are consumed in-memory by ph_nimitta Axis-6; material only if a
  downstream asset or retrieval tool needs the breakdown persisted.
- **Owner:** NATIVE decision (small). **Fix:** either (a) write the 339 DDL + populate, or (b) formally
  descope §3.5 and **delete the 339 stub**. Recommend (b) unless a consumer needs it.

### 🟠 MAJOR-3 — 5 dead migration stubs pollute the ledger permanently
- **Evidence:** `333_phala_rectification`, `334_phala_rectification_best`, `337_phala_outlook`,
  `338_*`, `339_*` are comment-only placeholders left behind when assets were renamed mid-build. They
  apply as no-ops but each gets a permanent `_migrations_applied` row, and duplicate numbers (two 333s,
  two 334s, two 337s) violate migration hygiene (the two-174-trap class of confusion).
- **Impact:** Not a runtime failure, but a hygiene + auditability defect; the duplicate numbers will
  mislead any future migration author.
- **Owner:** SWARM (autonomous), but **coordinate with B1/M2**: 338 must be *filled* (B1), not deleted;
  339 deleted-or-filled (M2). **Fix:** delete `333_phala_rectification`, `334_phala_rectification_best`,
  `337_phala_outlook`; fold 338 into B1; resolve 339 per M2. Net: one file per number, all real DDL.

### 🟠 MAJOR-4 — Hardcoded `/Users/Dev/Vibe-Coding/...` absolute paths break CI
- **Evidence:** 8 source `.py` files hardcode the macOS worktree absolute path, incl. tests
  (`tests/test_u1_dasha_consensus.py`, `tests/l2/test_b6_eval_harness.py`) and 6 scripts
  (`citation_graph_builder.py`, `governance/serialize_build_state.py`, `governance/v13_production_gate.py`,
  `run_bg_texts_additive.py`, `rebuild_ga_sensitive_ga_strength.py`, `invariants_l1.py`).
- **Impact:** These FAIL in any CI container (path doesn't exist) — exactly the failure reproduced in
  this audit. **This is why "211 tests pass" was true only on the swarm's macOS worktree.** CI-green
  (the merge gate) cannot be reached until these are fixed.
- **Owner:** SWARM (autonomous). **Fix:** replace each hardcoded path with a repo-root-relative resolver
  (`Path(__file__).resolve().parents[N]` or a `REPO_ROOT` env/fixture). Note: some predate L4 (governance
  scripts) — fix at least the L4-touched test files to unblock the gate; flag the rest.

### 🟡 MINOR-5 — `test_phala_outlook.py` references the retired table name
- **Evidence:** A `test_phala_outlook.py` exists but the table is `phala_phaladesa`. Stale test name
  tracking the dead stub.
- **Owner:** SWARM. **Fix:** rename to `test_phala_phaladesa.py` and point at the real table, or delete
  if duplicative of the wave-7 suite.

### 🟡 MINOR-6 — Test-count self-report inconsistency
- **Evidence:** PR title "153+", body/report "211"; this audit counted 2,913 `def test_` repo-wide and
  281 in the ph_/U sample. Cosmetic, but signals the self-report wasn't reconciled.
- **Owner:** SWARM. **Fix:** report the real number from a clean CI run (after MAJOR-4).

## §3 — Corrections to the prior (GitHub-based) PR #328 review
| Prior call | Corrected finding |
|---|---|
| B1: "337 stub → runtime crash" | **WRONG.** `337_phala_phaladesa.sql` (4,961 B) creates the table; the writer targets `phala_phaladesa`. `337_phala_outlook` is a dead stub, not the live table. No crash. |
| B2: "rectification descoped to anomaly registry" | **PARTLY WRONG.** Not a clean descope — the rectification migrations exist as dead empty stubs alongside the real `phala_sodhana` anomaly-registry DDL. The real question (MAJOR-3 + the open D41 scope) stands, but framed correctly: dead stubs to delete + confirm anomaly-registry IS the intended ph_sodhana scope. |
| B3: "CI not run" | **CONFIRMED + sharpened.** CI cannot pass until MAJOR-4 (hardcoded paths) is fixed. |

> **Open native question carried from D41 (still real):** ph_sodhana was built as a *prediction-anomaly
> registry*, not *birth-time rectification*. Migration 333_phala_sodhana + the writer are real and
> high-quality AS an anomaly registry. Confirm: is the anomaly-registry the intended final scope of
> ph_sodhana (rectification formally dropped), or must birth-time rectification be added? This is the
> one product-scope decision; everything else is mechanical.

## §4 — NATIVE DECISIONS (locked 2026-06-22)
- **D-R1 — ph_sodhana = KEEP BOTH.** The prediction-anomaly registry (as built, migration 333_phala_sodhana
  + 334_phala_suddha_sodhana) is RATIFIED as final. **ADD birth-time rectification as a DISTINCT capability**
  per the D41 spec: PyJHora ascendant scan over candidate birth times, scored against LEL life events,
  leakage-firewall, confidence interval, NO-AUTO-OVERRIDE (staged for one-click native adoption; canonical
  chart never auto-mutated — B.10). The dead `333_phala_rectification` / `334_phala_rectification_best`
  stubs are **FILLED with real rectification DDL** (not deleted) — they become the rectification tables.
- **D-R2 — U3 §3.5 per-current breakdown = DROPPED.** Currents are consumed in-memory by ph_nimitta Axis-6;
  no persistence consumer. Delete the empty 339 stub. (Currents enrichment logic itself stays — it exists + passes.)
- **N4 BOUNDARY (reaffirmed):** the whole of L4 + U2 stays bounded at level-4 (Sūkṣma). NO Prāṇa, NO
  `chart_dashas_prana`, NO level-5 persistence — anywhere. U2 is lifetime-horizon over existing N1–N4 parvas only.

## §5 — Remediation activity plan (ordered, decisions folded in)
| # | Activity | Severity | Owner | Gate |
|---|---|---|---|---|
| R3 | Implement **U2** (N4-bounded): extend `ka_sangam` horizon 5y→lifetime (coarse grain, bounded rows), re-run `ka_jivana_parva` scoring so `avg_effective_score` is non-null (739 parvas), write real 338 `kala_convergence.horizon_tier` DDL, re-seal L3, `[verify: prod]` | BLOCKER-1 | SWARM | hard |
| R4 | **Build birth-time rectification** (D-R1): fill 333_phala_rectification + 334_phala_rectification_best with real DDL; build the rectification writer(s) — PyJHora ascendant scan vs LEL, leakage-firewall, NO-AUTO-OVERRIDE, staged adoption, canonical chart NOT mutated. Anomaly registry untouched. | MAJOR (new build) | SWARM | hard |
| R5 | Fix **hardcoded /Users paths** in L4-touched test/script files (repo-root-relative resolver) | MAJOR-4 | SWARM | hard (CI gate) |
| R6 | **Stub cleanup:** delete 337_phala_outlook + 339 (D-R2); confirm 338 filled (R3) + 333/334 filled (R4). Net: one real file per migration number, zero dead stubs. | MAJOR-3 | SWARM | hygiene |
| R7 | Rename/repoint `test_phala_outlook.py` → `test_phala_phaladesa.py` (real table) | MINOR-5 | SWARM | minor |
| R8 | Run **full CI green** (both images build, pytest, migrate apply on fresh DB) on head SHA + reconcile test count | MINOR-6 + B3 | SWARM | hard (merge gate) |
| R9 | **HARD VISUAL SEAL** (post-merge): Cloud Run revision == merge SHA; Phala panel shows 8 assets lit with real counts + the rectification tables populated; zero errors — on prod AND localhost | — | SWARM | seal gate |

**Critical path to merge:** (R3 U2 ‖ R4 rectification ‖ R5 paths) → R6 stub cleanup → R8 CI green → merge → R9 visual seal. R3/R4/R5 are file-disjoint and run in parallel. R7 is trivial cleanup alongside.

## §5 — Bottom line
This is a **strong, largely-complete, contract-clean build** — the writers, anti-drift, model-policy
enforcement, U4 chart-generality, and migration DDL are all genuinely solid. It is **not mergeable as
shipped** for two real reasons: **U2 lifetime enrichment was never built** (BLOCKER-1) and **hardcoded
absolute paths block CI-green** (MAJOR-4), plus stub-cleanup hygiene. None of the catastrophic risks I
worried about from GitHub (missing tables, broken auto-discovery, drift, Anthropic calls) are real. The
fix set is well-bounded: one upstream writer (U2), a path sweep, a stub deletion, a CI run, and one
native scope confirmation.

---
*End of L4_PHALA_CODE_AUDIT_REMEDIATION v1.0. Ground truth = the worktree, not GitHub. Two real
blockers (U2 unbuilt; hardcoded CI-breaking paths), bounded hygiene, one native scope call. The rest
is solid.*
