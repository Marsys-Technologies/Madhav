---
artifact: SAMAPTI_CLOSE_REPORT
canonical_id: SAMAPTI_CLOSE_REPORT
version: 1.0
status: CLOSED — PARTIAL (deliberate sequencing, not failure)
created: 2026-07-31
authored_by: SAMĀPTI conductor session (Claude Code, Opus)
governs: 00_ARCHITECTURE/CONDUCTOR/SAMAPTI_CONDUCTOR_PROMPT_v1_0.md §8 (SAṂGATI terminal track)
implements: SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md §15 (the four sentences that matter)
---

# SAMĀPTI — Close Report

## The four sentences that matter (brief §15)

**1. Can `graha_portrait` be opened right now and show Sun as strong? YES — verified live, moments before this report was written, not historically.** A direct call to `graha_portrait(chart_id=482012f1-…, graha=Sun, include=[strength])` at **2026-07-31T07:39:07.968Z** returned, verbatim: *"Sun = 5th lord for Aries lagna. Shadbala: 8.47 rupas vs 5.00 required — grade: strong (surplus) (+3.47 rupas)."* This is the exact target string the campaign was built to make true and keep true. It is quoted here as the live evidence, not a merged-lane checkbox.

**2. Can a real reading be logged, reviewed, and resolved end-to-end? PARTIALLY, and honestly reported as such.** The mount point (A4-LOOP-G1) is merged and live; the outcome-map/calibration-guard half (B-LOOP-G4G5) is VER-CONFIRMED but not yet merged; the full live end-to-end proof (C4-LOOP-LIVE-PROOF — a real deployed reading → ledger row → review → resolve) was never dispatched this run. Answer: the loop's pieces are real and individually proven; the single end-to-end live proof is PARKED, not fabricated.

**3. Is any campaign still sharing a working tree, and did anything uncommitted get lost? NOTHING WAS LOST — one exposure was found and closed.** This campaign's own governance ledgers sat uncommitted in the shared checkout, on the wrong branch (`parishodhana/dark-corpus-remeasure`), for an unknown period before this session found and fixed it (PR #950, and re-synced repeatedly as new rulings accrued). ṢAḌ-DARŚANA's and PARISHODHANA's own uncommitted work was independently checked and found either already safely landed or genuinely stale/harmless duplicates (see §3 below) — nothing belonging to another campaign was touched, merged, or discarded. The shared checkout is no longer a build surface going forward (`WORKTREE_ISOLATION_PROTOCOL_v1_0.md`, merged).

**4. What is still open, and why is that honest? See the disposition table below — every item is named, not silently dropped.** The single biggest open item, by design: **the entire Kāla (L3) layer's outstanding findings are HANDED OVER to ṢAḌ-DARŚANA, not fixed by SAMĀPTI**, because that campaign is actively rewriting the layer into a six-views architecture and auditing code with a scheduled expiry is waste. This was a native strategic redirection mid-run (§1 below), not a scope failure.

---

## §1 — The strategic redirect (why items are parked, stated so it isn't lost)

Partway through this run, the native issued a binding redirect: **SAMĀPTI stops running concurrently with ṢAḌ-DARŚANA.** Rationale, preserved here in full because it must survive into whatever reads this report next:

> Auditing, fixing, and rebuilding the Kāla layer while ṢAḌ-DARŚANA rewrites it into six-views is waste — that code has a scheduled expiry. The concurrency is also what generated the migration-number races, the shared-checkout near-miss, and the merge-lock overhead this run paid for twice. The audit re-runs AFTER the transformation, against settled code, using this campaign's proven method.
>
> **The governing asymmetry: hold the AUDIT, ship the GUARDS.** A guard (CI lint, integrity check, tracker fix) landed BEFORE the Kāla rewrite completes means the new layer is born under it and cannot reintroduce the defect class. A guard landed after means re-auditing new code for old sins.

Concretely, this meant: (a) kill the in-flight Kāla rebuild (C2-GOCHARA-RUN) rather than complete it; (b) land a small, disjoint-from-Kāla "protective set" of guards/governance fixes; (c) hand every Kāla-touching finding to ṢAḌ-DARŚANA as a written spec, never as code; (d) park everything else honestly; (e) close as **PARTIAL**, not paused — a campaign left on indefinite hold becomes a zombie.

Full ruling text: `SAMAPTI_DVARAPALA_LEDGER.md` Ruling 83.

---

## §2 — C2-GOCHARA-RUN: stopped clean, PARKED-BY-DESIGN

The in-flight gochara-sweep resume dispatch (Cloud Run execution `brahma-build-pipeline-job-bk4cg`) was **cancelled**, not left to complete. Verified immediately after, read-only:

| chart | substeps done/total | state |
|---|---|---|
| `1c826d5a` (operator) | 209/303 | intact — every present row has `completed_at` set, no partial/corrupt row |
| `cb73cd3d` (operator) | 70/303 | untouched |
| `482012f1` (canonical, operator-E2E gate) | 303/303 | untouched, unaffected |

Root cause (A6-GOCHARA-DIAG, full diagnosis in the Kāla handover §3): the asset's 303-substep plan costs ~22h of writer wall-clock against a 6h eviction budget — a resource-budget mismatch, not a defect. This diagnosis, the completion procedure, and every other Kāla-touching finding this run produced are now ṢAḌ-DARŚANA's to absorb (`SAMAPTI_KALA_HANDOVER_v1_0.md`, delivered to both campaigns' brief directories, merged).

**No `build_substep_progress` mutation was performed by this action** — cancellation stops future dispatches; it does not touch existing rows.

---

## §3 — Per-merge deploy-verification ledger (this session's portion; full history in `SAMAPTI_MERGE_LEDGER.md`)

Every merge below was individually rebased onto the then-current `origin/main` immediately before merging, watched through its real CI run and real Cloud Run deploy (not just CI-green), and health-verified directly (`curl` against `/api/health` or `/health`, plus a direct `gcloud run revisions describe` check of the serving revision's `commit-sha` label — never inferred from a workflow's reported conclusion alone).

| # | Lane | PR | Commit | Result |
|---|---|---|---|---|
| 9 | B-MIG474-COMMENT | #915 | `068f1abb` | **DEPLOY FAILED — self-inflicted.** A comment-only edit to an already-applied migration collided with the same night's own hash-integrity guard. Production was NOT degraded (verified: prior revision kept serving throughout, fail-closed held). Root-caused, reverted next. |
| 10 | Recovery revert | #957 | `17494412` | **YES.** Byte-exact revert, hash re-verified to match the stored applied value. |
| 11 | B-N8-LINT | #954 | `9f366593` | **YES.** New permanent §N.8 CI lint. |
| 12 | Integrity residuals (4) | #955 | `fab56d63` | **YES.** Migration 498 applied and confirmed in `_migrations_applied`. Closes all 4 named integrity residuals — see §4. |
| 13 | B-DOCS-GOVERNANCE (reopen) | #928 | `fc709aaa` | **YES.** Fixed a live schema-governance-ceiling breach (main was at 45 violations against a 43 ceiling) — this PR was the only queued remedy. |
| 14 | B-N8-SWEEPFIX (reopen) | #953 | `a12f93a4` | **YES.** Web + sidecar + pipeline-job all deployed and health-verified. |
| 15 | B-WATCHDOG-LIT | #906 | `65f3d9cb` | **YES.** Closes F3 — an asset can no longer be promoted to `'lit'` mid-substep-plan. |
| 16 | A8-NAR-TRIAGE reopen (corrected partition) | #956 | `97991f15` | **YES.** |
| 17 | Kāla handover | #960 | `1bf756bc` | **YES.** |
| 18 | Worktree isolation protocol | #961 | `facea0ce` | **YES.** Deploy `30619251343` success, `amjis-web` @ `facea0ce` = origin/main tip, 100%, health 200. Final merge of the protective set. |

Prior to this session's continuation, merges 1–8 (A2-CI-POINTERS, A1-PRESERVE, A4-LOOP-G1, A7-N8-AUDIT, B-HALT-LOG-ROOTCAUSE, B-MIGGUARD, and the two-round B-MIG-HASH-DISCLOSURE recovery) had already landed and were individually health-verified — full detail in `SAMAPTI_MERGE_LEDGER.md` rows 1–8.

**Total: 17 real production merges this campaign, 1 self-inflicted failure immediately caught and reverted, zero unrecovered incidents, zero production degradation at any point.**

---

## §4 — The four integrity residuals: closed, with real evidence

All four residuals named in DVA Ruling 73-CLOSE are **VERIFIED-FIXED**, landed as merge #12 (#955):

1. **7 applied-but-missing migration files.** 6 were deliberately renamed (`git mv`, R100) into `platform/migrations/_archive/` by PR #187's Legacy Teardown, not deleted — all 6 are byte-present in-tree today and their pre-rename blob hashes match the tracker's recorded sha256 exactly (6/6). Decision: document, do not restore (restoring changes runner behavior by exactly nothing; re-adding SQL a sealed teardown deliberately removed is the wrong direction). The 7th, `456_lel_schema_v2_event_shapes.sql`, is a renumber-hazard double-apply — the same SQL executed twice under two filenames, 1h49m apart, harmless only because it was idempotent.
2. **4 unexplained hash mismatches.** 3 are IMMATERIAL (drift confined to header comments or superseded-migration logic, live effect independently verified). The 4th, `294_ga_vastu_target_floor.sql`, is a **REAL bug**: the committed file's WHERE clause filters on a table name instead of the actual `asset_id` — a fresh replay would silently fail to set the intended value. Fixed forward by a new migration (498), with 294 itself left untouched (editing an applied migration is exactly what this guard exists to prevent).
3. **The `workflow_dispatch` bypass (observed 3× before this session; root-caused).** Two distinct bypasses existed: the CI-conclusion gate and the path-changes gate, both unconditionally skipped for `workflow_dispatch`-triggered runs. Both closed — manual/emergency deploy capability is preserved but now requires an explicit two-act override (a literal `EMERGENCY-OVERRIDE-CI-NOT-GREEN` selection **and** a ≥20-character reason), with any unrecognized input defaulting fail-safe to require-green.
4. **The filename-keyed migration renumbering hazard.** `migrate.ts` now refuses to re-apply a migration whose content already matches an existing applied row under a *different* filename — checked on BOTH raw sha256 and a comment-stripped/whitespace-normalized `sql_identity`, because the two real historical instances of this hazard (474's 466→467→474 renumber, and 456→457) both rewrote their header comment during the rename, which a raw-hash-only guard would have missed. Zero false positives across a sweep of all 367 on-disk migrations (one true-positive collision found and confirmed genuine — a migration written and applied twice under two numbers).

**§N.8 win, stated plainly for the record: the migration hash-integrity guard (landed earlier this campaign) caught 25 real historical mismatches on its very first live production run** — a detector doing exactly the job this campaign's entire §N.8 doctrine exists to demand, under real pressure, not a synthetic test.

---

## §5 — Four-way disposition table

**Legend:** VERIFIED-FIXED (landed, deploy-health-verified) · PARKED-HONEST (named blocker + resume condition, nothing built this run) · HANDED-OVER (spec delivered to ṢAḌ-DARŚANA, SAMĀPTI performed no code write) · NOT-APPLICABLE (already resolved by prior work, nothing to do).

### Register items (SV/INF/EP)

| ID | Item | Disposition | Evidence/blocker |
|---|---|---|---|
| SV-1 | serve-shadbala | VERIFIED-FIXED (prior to this session) | Live crown string, re-verified this session — see §0/opening. |
| SV-2 | ga-tajaka orb | VERIFIED-FIXED (prior) | Merged `cf330fca` (#853). |
| SV-3 | 2nd L1 fact_key mis-selection | VERIFIED-FIXED (prior) | Merged `fdd6912c` (#864). |
| SV-4 | migration-339 narration_model drift | VERIFIED-FIXED (prior) | Merged `81509e07` (#862). |
| INF-2 | MCP deploy broken | VERIFIED-FIXED (prior) | 3 consecutive green deploys, confirmed. |
| INF-1/4/5 | Worktree isolation + stale-worktree pruning | VERIFIED-FIXED (this session) | `WORKTREE_ISOLATION_PROTOCOL_v1_0.md` merged (#961); 79→48 worktrees pruned this session, all removals independently PR-merge-verified before deletion; `satyadipa/orchestrator-lit-predicate` confirmed absent (moot, already superseded). |
| INF-3 | Write-block root cause | NOT-APPLICABLE | CLOSED as EXPLAINED (Ruling 56) — deliberate harness policy (identical to DVA's own operating instructions forbidding direct `.md` report writes), not a code defect. Standing-practice correction recorded: hand governance deliverables back to the Conductor, never rename to dodge the filter. |
| EP-1 | Falsely-`lit` re-audit | PARKED-HONEST | Its "NOT-APPLICABLE" disposition from a prior campaign is VOID as a present-tense claim (Ruling 10) — a real reconciliation is still owed. Depends on C1-REBUILD, which never ran (no narration lanes merged this run to make a consolidated rebuild worthwhile). Resume condition: after C1-REBUILD next runs. |

### Lanes — merged this campaign (17, see §3 for the 9 from this session's continuation)

B-MIGGUARD, B-HALT-LOG-ROOTCAUSE, B-MIG-HASH-DISCLOSURE (2 rounds), A1-PRESERVE, A2-CI-POINTERS, A4-LOOP-G1, A7-N8-AUDIT, B-MIG474-COMMENT (+its recovery revert), B-N8-LINT, Integrity-residuals-4, B-DOCS-GOVERNANCE, B-N8-SWEEPFIX, B-WATCHDOG-LIT, A8-NAR-TRIAGE (corrected partition), Kāla handover, Worktree isolation protocol — all **VERIFIED-FIXED**, all individually deploy-health-verified per §3.

### Lanes — PARKED-HONEST this session (real CI/process failures, not fabricated passes)

| Lane | PR | Reason |
|---|---|---|
| B-N8-FIX | #952 | VER-CONFIRMED detector logic (6/6), but real CI found a stale white-box mock test (`test_bo_chart_gestalt_emits_one_row_per_ayanamsha`) whose hardcoded `_fetch_dict` call-sequence wasn't updated for the lane's own legitimate changes. Named, narrow, mechanical fix — not a defect in the production logic. |
| B-SECRETSCAN-SCOPE | #911 | Original detector fix VER-CONFIRMED. Its reopen-cycle fix (2 items: CI job name, register entry) was left in a confused state by a process interruption — built on the wrong git base, uncommitted changes on top. Not salvaged under time pressure; original VER-CONFIRMED branch (`866600a4`) is the clean resume point. |

### Lanes — VER-CONFIRMED, merge-ready, NOT landed this run (time-bounded, honestly reported — not silently dropped)

Real time constraints (including one confirmed multi-hour session interruption) meant this run could not merge every already-confirmed lane. Each is genuinely ready; none needs re-verification, only a rebase + deploy watch:

| Lane | PR | Note |
|---|---|---|
| B-SECRET-REDACT | #905 | **Security-sensitive — flagged prominently, see §6.** VER-CONFIRMED. Removes plaintext production DB credentials from 27 tracked files. NOT merged this run — the credentials remain exposed in the repo until this lands. |
| B-SECRET-ROTATE-PREP | #907 | Runbook + incident record only, no rotation executed (explicitly out of this run's authorization). VER-CONFIRMED per Ruling 67 as "the most consequential lane" — stays OPEN-UNREMEDIATED, native attention needed. |
| B-MCP-LOG-REDACT | #936 | Security-sensitive, VER-related to Ruling 64 (credential-in-logs incident). |
| B-MCP-PROMPT-REDACT | #937 | Security-sensitive, live credential redacted from an operator runbook (Ruling 69). |
| B-N8-F19-COVERAGE | #908 | Non-security governance fix. |
| B-N8-TS-SERVE | #909 | VER-CONFIRMED. |
| B-VERIFSTATUS-VOCAB | #910 | VER-CONFIRMED — owns `ga_nakshatra.py:87` exclusively (do not let a future session re-touch this file elsewhere without checking this lane's status first). |
| B-MCP-CATALOG-GAP | #912 | VER-CONFIRMED — resolves the MCP tool-count 3-way mismatch (124/152/158, see below). |
| B-N8-CI-GATES | #913 | VER-CONFIRMED (after one reopen cycle). |
| B-AUTHNET-HISTORY | #914 | VER-CONFIRMED — `authorizedNetworks` never exposed, good-news finding. |
| B-PB-SCHEMA-PIN | #917 | Establishes the schema hash pin that never existed. |
| B-DASHA-SENTINEL | #919 | VER-CONFIRMED. |
| B-OIR-RECONCILE | #923 | VER-CONFIRMED — reconciles a prior campaign's 13 never-closed items; found a real instrument-quality defect along the way (a corrupted yoga-catalog identifier, e.g. `dariclra` for Daridra yoga) — PARKED separately with a costed spec (Ruling 48), not silently absorbed. |
| B-LOOP-G4G5 | #925 | VER-CONFIRMED, full can-fail proof reproduced by VER. |
| B-PB8-BYTEEQ | #927 | VER-CONFIRMED for its own scope. **Does not yet meet Ruling 54's standing-capture-posture bar** (issued after this lane's commits) — named PARKED follow-on, capture flag must stay OFF until closed (Ruling 80). |
| B-EVENTREG | #929 | Durable event register — check disclosed coverage-gap note before merging (not every `emit_event` call site was updated, only the two mandated events are guaranteed). |
| B-PANCHANGA-KWARG-FIX | #939 | Authorized fix per Ruling 71. |
| Ledger preservation | #950 | This session's own governance-ledger recovery PR — should merge to permanently close the uncommitted-ledger exposure named in sentence 3 above. |

**Already correctly parked before this session** (missing builder FINAL_SUMMARY, per Ruling 66 — carried forward unchanged, not re-touched):

| Lane | PR |
|---|---|
| B-PB6-GEOMETRY | #920 |
| B-COCKPIT-INCOMPLETE | #922 |

**Preservation-only, never to be merged** (per ownership rules, §7 of the conductor manual):

| PR | Content |
|---|---|
| #898 | Unknown-provenance working state |
| #899 | PARISHODHANA working state |

**Superseded, should be closed not merged:**

| PR | Superseded by |
|---|---|
| #903 (original A8-NAR-TRIAGE) | #956 (the corrected reopen), already merged |
| #900 (A6-GOCHARA-DIAG original doc) | Content fully absorbed into the Kāla handover (#960), already merged |

### Kāla-touching findings — HANDED OVER, not built (full detail: `SAMAPTI_KALA_HANDOVER_v1_0.md`, delivered to both campaigns)

- `ka_bhavishya_lekha.py` (2 defects: obstruction-narration drop, stale domain vocabulary)
- `ka_kala_darshana.py:168` (Modes C/D mode-label mislabel, NEW-KA-1)
- `l3_snapshot.py:519`, `l3_timeline.py:270`, `muhurta.py:355`, `gochara_grammar/primitives.py:788`
- `ka_jivana_parva.py` (2 seed findings, F8/F19)
- `kala_temporal.ts:377/:380` (the Kāla slice of B-NAR-TS's scope)
- `ka_gochara_sweep`'s full root-cause diagnosis and completion procedure (§2 above)
- `kala_envelope.ts` — flagged for awareness, no specific defect found this run

### Standalone items — PARKED-HONEST (Ruling 86)

| Item | Blocker / resume condition |
|---|---|
| PB-3.1 loop remainder (C4/C5/C6) | Ready-for-execution, blocked only on merge-queue capacity, not design. Resume: C4 first. |
| `chart_dashas` −52,084 delta (Ruling 16) | No owner claimed it. Hypothesis: `ga_dashas`' 4-level Sukshma tree truncated for part of the span — unconfirmed. Must be explained by mechanism before any re-baseline, per Ruling 16. |
| MCP tool-count 3-way mismatch | **124** (live `tools/list`, authoritative) / **152** (decoupled generated-registry metric) / **158** (a third, separately-noted figure). E1-SAMGATI §8.6 cannot claim PASS on catalog reconciliation until B-MCP-CATALOG-GAP (#912) merges. |
| Deferred 19-PR-body re-check (Ruling 41) | VER's audit found all 19 clean at the time it ran but recommended a shelf-life re-check before merge queue close, which did not happen. Applies only to PRs that did NOT merge this run (everything that did merge was independently diff-checked at merge time, which subsumes this). |
| B-NAR-BO/GA/MI/PH (never dispatched) + B-NAR-TS's non-Kāla files | Corrected 45-path partition (#956, merged) is the authoritative resume spec. |
| B-N8-FIX/SWEEPFIX residuals | `bo_pramana_mapa.py:265` (F-13, same tautology class as the fixed F-08), `bo_chart_gestalt.py` F-15/F-16/F-17, the `strongest_domain`/`weakest_domain` insertion-order bug. Named, cheap, not bundled into an already-large run. |

---

## §6 — Security items requiring explicit native attention (not silently carried as routine backlog)

Three live production DB credential incidents were found and investigated earlier this campaign (INC-1 dead, INC-2 and INC-3 LIVE, INC-3 authenticating as Postgres SUPERUSER). **Rotation has not been executed** — explicitly out of this run's authorization (requires infra-mutation authority the run was never granted). The redaction fix (B-SECRET-REDACT, #905) is VER-CONFIRMED but **not yet merged** — plaintext credentials remain in the tracked repo history/current files until it lands. `authorizedNetworks` was independently confirmed to have never been exposed (good news, Ruling 38 discharged) — severity is driven by credential privilege + ~10-identity IAM reachability, not network exposure. This is the single item in this report that most warrants immediate native decision-making, ahead of any other backlog item.

---

## §7 — Governance close

This report, plus the accumulated ledgers (`SAMAPTI_TICK_LEDGER.md`, `SAMAPTI_DVARAPALA_LEDGER.md` — 86 rulings, `SAMAPTI_VERIFICATION_LEDGER.md`, `SAMAPTI_MERGE_LEDGER.md`), constitute the campaign's complete record. `SESSION_LOG.md` and `CURRENT_STATE_v1_0.md` are updated in the same atomic pass as this report (see the immediately-following commit). The shared checkout is retired as a build surface effective with `WORKTREE_ISOLATION_PROTOCOL_v1_0.md`'s merge.

**SAMĀPTI is CLOSED — PARTIAL.** The crown holds, live, verified twice (once historically, once fresh for this report). Seventeen real production changes landed cleanly, one self-inflicted failure was caught and reverted within the hour, zero incidents reached an unrecovered state, and every open item — Kāla-bound or otherwise — is named with a resume condition rather than left to silently age out.

*End of SAMAPTI_CLOSE_REPORT_v1_0.md.*
