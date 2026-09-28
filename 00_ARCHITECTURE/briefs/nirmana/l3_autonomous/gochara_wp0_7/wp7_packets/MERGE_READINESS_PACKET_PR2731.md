# MERGE READINESS PACKET — PR #2731 (`l3/gochara-autonomous-wp0-7`)

- **Produced:** 2026-09-29, executor lane `l3/gochara-autonomous-wp0-7` @ `800057a73`
- **Governing:** ADK-0027 (native directive F-0, precondition 1 — deploy-before-flip),
  ADK-0028 (light-work scope; Cloud-Run-only century rebuild), ESCALATIONS.md E-020/E-021.
- **Scope of this packet:** readiness evidence for the NATIVE's merge of #2731 into `main`.
  Nothing here merges, applies, or flips anything.

---

## 1. CONFLICT RESOLUTIONS — merge commit `f95cf19af` (origin/main → this branch, 2026-09-29)

Merge authorized explicitly by F-0 (ADK-0027 §2: merge commit, not rebase, narrows
ADK-0010(iii) for this purpose only). Four files conflicted; all are docs/governance files.
Verification: recorded in
`platform/python-sidecar/scripts/kala_gochara_cutover/evidence/f0p2_horizon_parity_evidence.md`
(header: "origin/main merged in, PRAMĀṆIN-verified, pushed"). No standalone PRAMĀṆIN
artifact for the merge exists beyond that record.

| File | What conflicted | Resolution |
|---|---|---|
| `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` | Version counter collision: both sides appended changelog entries; `main` independently consumed v6.82 for JATAKA-PHASE-A-HARDENING while this lane used v6.81/v6.82. | Changelogs unioned; this lane's entries **renumbered to v6.88 / v6.89** with an inline note ("renumbered from v6.81/v6.82 at the origin/main merge — main independently used v6.82 for JATAKA-PHASE-A-HARDENING"). Head version set to **6.89**. No content dropped from either side. |
| `00_ARCHITECTURE/SESSION_LOG.md` | Both sides appended session entries at the tail (lane side +718 lines, main side +2151 lines in the conflicted hunk). | **Union of both sides' entries** (merged file carries +2866 lines in that region). Chronological append-only log — both histories preserved, no entry rewritten. |
| `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v2_0.md` | Migration-number floor in `may_touch` and step-4 schema row: `≥1075` (stale) vs `≥1071`. | Resolved to **`migrations ≥1071`** in both places — the correct numbering per the E-009 re-scan (the lane's WP10 relations begin at 1071). |
| `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` | Identical conflict to v2_0 (`≥1075` vs `≥1071` in `may_touch` and step-4 row). | Identical resolution: **`≥1071`**. |

All other merge content arrived cleanly (Jātaka/AI-console migrations 1120–1125 as expected;
`.github/workflows/deploy.yml` serving/deploy changes; Kṣetra packets; etc.).

## 2. CI STATUS (queried 2026-09-29 ~05:00 IST, post-merge HEAD `800057a73`)

`gh pr view 2731 --json mergeable,mergeStateStatus`:
**`mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED`.**

Fresh checks were triggered on the post-merge HEAD and are **mid-run**: several jobs are
still `pending` (Build Check, TypeScript src, Unit Tests, DB Integration Tests, Density
Census, Gate batteries chromium/mobile, ICR PR Gate, PRATIJÑĀ v4, Planner Regression).
Run logs for completed-failing jobs are not yet available ("run … is still in progress").

Completed so far:

- **PASS (sample):** K1+W1 PLAN-mode serving gates; D-08 pointer integrity; W0.6 unit
  batteries; W2 specificity; Coverage Gate; Registry Parity + fact_subject gate; Naming
  Governance; NO-LEAKAGE canary; Reducer tests; TAP-5/7/S-13; boot-time pointer
  validation; TypeScript platform-mcp; D-01b/c/d/e.
- **FAIL (5):** `D-01a — No Local Aspect Dict (WARN)`; `Earned-Signal Gate (§N.8)`;
  `Fact-Category Pinning Gate (§5 C.7)`; `Governance Gates (drift / schema / edge /
  native-literal / py-sidecar)`; `Secret Scan (unit 0b.2)`.

**Material finding for the Governance Gates failure:** the 12.10c staleness is confirmed
locally on the merged tree —
`python -m pipeline.orchestrator.provenance_inventory --check` reports
**"writer digest inventory is stale"** (`platform/src/generated/nirmana-writer-digests.json`
no longer fingerprints the merged writer sources). This is exactly what the 12.10c runbook
predicts for a merge that changes writer content, and is the likely root of at least the
Governance Gates failure. Whether it explains Earned-Signal / Fact-Category-Pinning /
Secret-Scan / D-01a failures is UNCONFIRMED until logs are available — treat those four as
open.

**CI is therefore NOT green. This alone is a stop item.**

## 3. DEPLOY MIGRATION LIST — `migrate.ts --dry-run` against production

Method: fresh `amjis-pipeline-db-url` from Secret Manager
(`gcloud secrets versions access latest … --project=madhav-astrology`), own
`cloud-sql-proxy` on `127.0.0.1:55440` (the native's 5433 proxy never touched), role
`amjis_app`, `--dry-run` only; proxy torn down after. Only pre-existing DVA-RULING-73
hash disclosures were emitted (informational, all pinned).

**Dry run — would apply (exact list):**

```
1071_kala_gochara_windows_generation_guard.sql
1072_kala_b1_registry_truth_and_sweep_protection.sql
1086_nirmana_l1_gochara_g10_ga_strength_contributor_digest_spec.sql
```

Assessment:

- **1071, 1072 — cherry-picked-but-unapplied (known-expected).** Standing instruction:
  DO NOT apply locally (1072 unapplied is load-bearing for conjunct (j) — runbook §4;
  1071's guard is enforced on-branch in rehearsal only). **STOP-LEVEL QUESTION FOR THE
  NATIVE:** merging #2731 makes the deploy runner apply 1071+1072 to production. Whether
  that deploy-time application is intended is the native's call — stated, not answered here.
  Note the interplay recorded in runbook §4: applying 1072 flips `target_table` to
  `kala_gochara_windows_v2` and **breaks conjunct (j)** of the step-5 re-pin (1091) unless
  coordinated.
- **1086 — ga_strength digest spec.** OPEN native-coordination item: F-0 requires the
  **native** to confirm with the **L1 lane** that applying 1086 at deploy is intended.
  Recorded as OPEN; not confirmed by this lane.
- **Frozen seven (1080, 1081, 1082, 1083, 1084, 1087, 1091) and 1150 — VERIFIED ABSENT
  from the pending list.** Production `_migrations_applied` already carries 1080–1084,
  1087, 1091 (2026-09-24) and 1150 (2026-09-28) — consistent with the f0p2 evidence
  step-1 record. ✓
- **Nothing unexpected appears.** Pending set is exactly {1071, 1072, 1086} — no other
  surprises; the in-branch Jātaka/AI-console migrations 1120–1125 show as already applied
  in production (applied on main's own deploys) and do not appear.

## 4. 12.10c RUNBOOK STATUS

`MERGE_HYGIENE_12_10c_RUNBOOK.md` — **documented 2026-09-27, NOT executed.** Nothing in it
may run before the second merge lands; it still has not run.

**Changed second-merger dynamics.** The runbook was written for "whoever merges second
between this branch and the L0 lane." That framing is now overtaken: F-0 had **main merged
INTO this branch** (merge commit `f95cf19af` exists; the merged tree exists here, now).
Consequences:

1. The runbook's ordering constraint ("run against the merged tree after the merge commit
   exists") **is already satisfiable on this branch** — the digest staleness it predicts is
   already live (§2: `provenance_inventory --check` fails on this tree).
2. **Duty assessment:** steps 1 (writer digests) and 3 (capability-estate census) are
   file-only regenerations of the merged tree and now belong to **this lane** — running
   them on-branch ahead of the native's merge is what makes "CI green on the second merge
   without a manual pin fix" achievable at all; leaving them to the native's merge of #2731
   would guarantee red CI here. Step 2 (L3 pin re-admission) requires the frozen campaign
   manifest (read-only evidence-DB access), review artifacts, and commit values filled from
   the tree at that time; it can also be prepared on-branch but its immutable commit values
   must be taken at execution time, never copied. **Recommendation for native ruling:**
   authorize this lane to execute 12.10c steps 1–3 on-branch now (light work; one file-only
   step + one census codegen + one read-only-DB pin step), rather than leaving all three to
   the merger. Until that ruling lands, the regeneration is recorded as **this lane's duty,
   pending native go**.
3. If the L0 lane still merges after #2731, the runbook's original second-merger hygiene
   applies to THAT merge unchanged.

## 5. F-0 PRECONDITIONS TABLE

| Precondition | Status | Evidence / note |
|---|---|---|
| **Deploy-before-flip** (P1): native merges #2731 + deploys → DEPLOY_SHA verification from the service env (Trap 103, not deploy metadata) → soak trigger #0 | **PENDING — native territory.** Merge/deploy is the native's; DEPLOY_SHA verification follows deploy. **Soak trigger #0: ADDED** by this packet session — `platform/python-sidecar/scripts/kala_gochara_cutover/step09_soak_checklist.md` abort-trigger list now carries trigger 0 (within minutes of flip, read-only served windows must return the flipped generation's rows with its own manifest provenance, else immediate `--reverse`). | ADK-0027 §2; step09_soak_checklist.md (this branch) |
| **Horizon parity** (P2): century rebuild via Cloud Run Job `brahma-build-pipeline-job`, only AFTER #2731 merge+deploy (ADK-0028); local century enumeration prohibited | **PENDING — blocked on P1.** Default governs (full-'3.0'-horizon rebuild, label `'4.1'`, both charts; horizon [1984-02-05, 2084-02-05) per f0p2 evidence step 1); no narrowing ruling found (step-0 exception check, recorded). | ADK-0028 §1/§3; `evidence/f0p2_horizon_parity_evidence.md` |
| **Disclosure 3 (R240)** recorded: registered ka_gochara writer emits `'2.0'` only; `'4.0'`/'4.1' producible solely by cutover scripts | **RECORDED** (ADK-0027 §3; handed to the L3 plan as a finding). Non-blocking. | ADK-0027 §3 |
| **Kṣetra writer change + migration 1084 land with this PR** | **CONFIRMED on-branch** — 1084 is among the frozen seven, already applied in production (2026-09-24) and absent from the deploy pending list; the Kṣetra writer change rides #2731's diff. | ADK-0027 §3; §3 dry-run above |
| **Chart-2 superseded `'4.0'` candidate rows retained** per ADK-0028 §4 (candidate-only, untouched by serving, replaced by the `'4.1'` build) | **RECORDED / standing.** Production state per f0p2 step-1: chart 2 manifest `4dc6c74c…` candidate, 138,836 contacts + 48 coverage, 0 windows. Deliberate retention, not drift. | ADK-0028 §4; f0p2 evidence step 1 |
| **Chart-1 `'4.0'` label burned** (rebuild as `'4.1'`) | **CONFIRMED.** Manifest `d54d899b…` = `rolled_back`; zero `'4.0'` rows for chart 482012f1 anywhere; re-attempt under label `'4.1'` only. | ADK-0027 §1/§4; step09 checklist "Burned label" |

---

## HEADLINE VERDICT: **HOLDING**

Stop items, in order:

1. **CI not green on post-merge HEAD** — 5 failing checks (Governance Gates, Earned-Signal,
   Fact-Category Pinning, Secret Scan, D-01a-WARN) plus a large pending set. Writer-digest
   staleness (12.10c step-1 artifact) is confirmed locally on the merged tree and is the
   likely root of the Governance Gates failure; the other four failures are UNCONFIRMED
   pending logs.
2. **12.10c regeneration duty now sits with this lane** (the merged tree exists on-branch);
   steps 1–3 have NOT run. Awaiting native go to execute them on-branch (recommended) —
   without them the second merge cannot reach green CI.
3. **STOP-LEVEL: deploy runner would apply 1071 + 1072 at merge** — intended? (1072 flips
   `target_table` and breaks conjunct (j) if applied uncoordinated; standing instruction is
   DO NOT apply locally.) Native decision required.
4. **OPEN native coordination: 1086** — the native must confirm with the L1 lane that
   applying it at deploy is intended. Not confirmable by this lane.

Non-blocking, recorded: Disclosure 3 (R240); chart-1 `'4.0'` burned; chart-2 candidate
retention; soak trigger #0 added to `step09_soak_checklist.md`; frozen seven + 1150 verified
absent from the deploy pending list.

Next native actions: rule on stop items 2–4; merge + deploy #2731 when green; then
DEPLOY_SHA verification → Cloud-Run century rebuild → flips under trigger #0 + soaks
(ADK-0028 amended sequence).
