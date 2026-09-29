# MERGE READINESS PACKET — PR #2731 (`l3/gochara-autonomous-wp0-7`)

- **Produced:** 2026-09-29, executor lane `l3/gochara-autonomous-wp0-7` @ `800057a73`
- **Refreshed:** 2026-09-29 second pass (Pravāha A0.3/A0.4) @ **`650846852`** — second
  origin/main merge `8eeeb6e2a` landed (A0.2), pins re-admission executed under **D-E022**
  (A0.3), **CI fully green**. Sections 2, 2c, 3, 4 and the verdict supersede their first-pass
  content where marked; unmarked first-pass content stands.
- **Governing:** ADK-0027 (native directive F-0, precondition 1 — deploy-before-flip),
  ADK-0028 (light-work scope; Cloud-Run-only century rebuild), ESCALATIONS.md E-020/E-021/E-022,
  **D-E022** (native, 2026-09-29: "Accept all recommendations." — pins re-admission at the
  #2731 merge authorised per MERGE_HYGIENE_12_10c_RUNBOOK).
- **Scope of this packet:** readiness evidence for the NATIVE's merge of #2731 into `main`.
  Nothing here merges, applies, or flips anything.

---

## 1. CONFLICT RESOLUTIONS — merge commit `f95cf19af` (origin/main → this branch, 2026-09-29)

### 1a. Second merge — `8eeeb6e2a` (origin/main `55ec5e355` → this branch, 2026-09-29, Pravāha A0.2)

A second origin/main merge landed after the first-pass packet. Only conflict:
`00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, resolved as union — this lane's changelog entries
renumbered v6.87/6.88/6.89 → **v6.89/6.90/6.91** with in-text renumber disclosure, frontmatter
version **6.91**, main's v6.87/v6.88 kept verbatim. `SESSION_LOG.md` pure additions
(858+/0−). All other 36 merge-changed files byte-identical to main; zero gochara-scope
overlap; merge commit, no history rewrite. Independently PRAMĀṆIN-verified (5/6 claims
fully, one count corrected and accepted). First-pass conflict table below stands for `f95cf19af`.

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

## 2. CI STATUS

### 2.0 CURRENT (second pass, HEAD `650846852`, 2026-09-29 ~12:05 UTC)

**`gh pr checks 2731 --watch` exit 0: every check green — 1514 pass, 0 fail.**
`gh pr view 2731 --json mergeable,mergeStateStatus`: **`MERGEABLE` / `CLEAN`**.

Repairs executed in this pass (commits `442f1ed9`, `f4cba9d6`, `ec98215b`, `6f145dd87`,
`ad22bef06`, `19a8fffce`, `650846852`):

1. **Pins re-admission (12.10c step 2) under D-E022** — see §2c (RESOLVED).
2. **Pre-existing lane test failures** (red on the lane before either merge; verified failing
   at `23b3d4953` and at merge `8eeeb6e2a`, green on main) — all repaired by re-pointing
   tests at the lane's ruled truth or fixing genuinely non-compliant code, never by weakening:
   - `test_swiss_state_boundary.py` — `gochara_kernel/knots.py` `calc_sidereal_lon` (the
     kernel's single Swiss seam) was calling Swiss without the DP-SD-010 serialized boundary:
     **code fixed** (`@serialized_swiss_state`), and the G-10 prastara owner
     (`ga_strength_writer._derive_ashtakavarga_prastara`, already decorated) registered in
     `EXPECTED_OPERATION_OWNERS` (G-10 / ruling sheet M-7 / N-21).
   - `test_mr06_cutover_durability.py` — re-pointed to the ruled ka_gochara identity
     (`kala_gochara_windows_v2`, generation `'2.0'`; Kāla B1 correction 2026-09-22, recorded
     verbatim in `ka_gochara.py`'s module docstring), with **new negative assertions** that
     ka_gochara never targets the protected `kala_gochara_windows` corpus.
   - `tests/l3/test_ka_gochara_resonance.py` — re-pointed to the M-6 taxonomy
     (`bhava_arudha` target type + 10 run()-level M-6 derived rows; WP1_CONTRACTS §2.2
     items 9–11; count assertion now computed from the writer's own constants: 297+10=307).
   - `beyond_acarya_acceptance.test.ts` — hashes advanced per the file's own v-succession
     convention: new immutable artifact `BEYOND_ACARYA_ACCEPTANCE_v11.json` (v10 preserved
     as immutable historical; metrics unchanged — only `content_hash`/`report_hash` moved via
     the ka_gochara re-identification + §N.6 snapshot regen `68a56814a`).
   - `route_golden_stream.test.ts` — two baselines (`branch-deep-dive`,
     `branch-completeness-receipt`) regenerated via the harness's own
     `PARIPRASHNA_PORTS_BASELINE=write` convention; only the embedded closure-receipt hash
     moved (capability-snapshot cascade); the other 35 baselines byte-identical.
3. **Digest cascade from the knots.py fix** — handled with a **second append-only L3
   successor** (`l3:ad22bef06784:d1bf773c4d94`, source `ad22bef06`) under the same D-E022
   authority; the first successor is archived whole and immutable (asserted in both test
   suites). Pin/receipt test suites extended per the "rewind, do not weaken" convention:
   `test_nirmana_analysis_layer_pins.py` 69 passed / 3 skipped;
   `nirmana-analysis-receipts.test.ts` 13 passed.

First-pass sections 2a/2b below are kept for the record.

### 2a. State at packet time (HEAD `800057a73`, queried ~05:00 IST) — SUPERSEDED

Five FAIL: `D-01a (WARN)`, `Earned-Signal Gate (§N.8)`, `Fact-Category Pinning Gate
(§5 C.7)`, `Governance Gates`, `Secret Scan (unit 0b.2)`; rest pending/passing.

### 2b. Resolution pass (2026-09-29, executor; fixes committed as `bd5c34fb0` +
`68a56814a`, remote re-run at those SHAs)

| Check | Root cause | Fix | Local evidence | Remote after push |
|---|---|---|---|---|
| D-01a No Local Aspect Dict (WARN) | 2 NEW violations: (i) `ga_strength_writer.py` allowlist entry pinned at line 224 while this branch's G-10 insertions above shifted the byte-identical `_DRIK_ASPECT_OFFSETS` dict to line 230; (ii) `gochara_kernel/convention.py:45` `SPECIAL_DRISHTI_DEG` — this lane's NEW pinned doctrine (N-14 RULED: nodes cast NO dṛṣṭi), for which the suggested oracle `brahmagyan.aspects.get_graha_aspects()` carries the OPPOSITE nodal convention (aspects.py:26) — importing it would violate the ruling. | Sanctioned allowlist mechanism: line 224→230 update (byte-identity verified vs `origin/main:224-232`) + new entry for `convention.py:45` citing N-14/WP1 §7 and why the oracle cannot be imported. **Committed independently by a parallel lane session as `25f5dd6cb` with identical content; my working-tree edit matched it exactly and was dropped.** | `check_no_local_aspect_dict.py`: 0 new violations (3 allowlisted). PASS. | PASS (not in the failing set at `bd5c34fb0`/`68a56814a`) |
| Secret Scan (unit 0b.2) | 13 NEW `pg_conn_string` findings — all the lane's disposable-DB DSNs (`postgresql://wp6:<pw>@localhost:…`, password a throwaway dictionary word) in 7 docs/evidence files + 6 test defaults. Not real credentials (throwaway docker containers), but literal credential-shaped strings. | Docs/evidence: password masked to `***` (scanner-sanctioned masked form; history not falsified — the recorded commands now show a placeholder, the DBs were torn down regardless). Tests: default password renamed `disposable`→`local` (scanner's sanctioned weak-placeholder tolerance; env override unchanged). Scanner itself untouched; inherited register untouched. | `secret_scan.sh`: PASS (no new literal credentials); `--self-test` exit 0. Local gitleaks add-on reports 283 historical findings — NOT a CI gate (CI has no gitleaks; script comment documents this). | PASS |
| Earned-Signal Gate (§N.8) | 2 NON-ALLOWLISTED: `step07_flip_gates.py:75,89` — `ts_gate` (signal name, `_gate` suffix) bound to the constant `"NOT_RUN (route test lives in platform-mcp)"`. | Honest fix per the lint's own message: `"ts_gate": None` + explanation moved to non-signal field `ts_route_test`. No gate semantics changed; no allowlist growth. | `check_earned_signal.py`: 0 new (143 allowlisted). PASS; `--self-test` exit 0. Gochara battery 300 passed / 83 skipped. | PASS |
| Fact-Category Pinning Gate (§5 C.7) | 2 NON-ALLOWLISTED: `step06_enumerate_episodes.py:178` (fetch ALL rows of `sensitive_degree_check` to build a fact_id→subject lookup map) and `gochara_v3/context.py:646` (`_fetch_kakshya_boundaries` assembles per-subject dicts keyed BY fact_key across every key of the category). Both are set-valued whole-category reads; a fact_key pin would break them. | 2 AUDITED allowlist entries in `fact_category_pin_allowlist.json` following the repo's own precedents (`bo_upaya.py` set-of-keys; `get_kp_cusps.ts:140` multi-key assembler), pattern-keyed not line-keyed. Gate not weakened. | `check_fact_category_pinning.py`: 0 new (65 allowlisted). PASS; `--self-test` exit 0. | PASS |
| Governance Gates | TWO causes. (i) `provenance_inventory --check` stale on merged tree (12.10c step-1 artifact) — FIXED: runbook step 1 executed, `nirmana-writer-digests.json` regenerated, `--check` green. Also in this job: drift 79 (≤ ceiling 79, exit 3) PASS; schema_validator was exit 1 from ONE CRITICAL — the `L3-GOCHARA-WP0-7-ADK0018-20260927` SESSION_LOG entry embedded a `session_close_pointer` instead of an inline `session_close:` block — FIXED by inlining the canonical close YAML verbatim (now 42 violations ≤ 43, exit 3). (ii) **pins `--check` — STILL RED, see 2c.** | (i) executed; (ii) stopped — native authority required. | `provenance_inventory --check` exit 0; `drift_detector` 79/exit 3; `schema_validator` 42/exit 3. | FAIL — remote log confirms the ONLY remaining failure is the pins step ("L1 active: writer_inventory_sha256 is stale … L3 active: … changed_assets do not match exact delta") |
| Density Census (§N.6) | `capability_knowledge.snapshot.json` stale on merged tree (planner capability content arrived via main merge). | `npm run codegen:capability-knowledge -- --generated-at=2026-09-29T00:16:48Z` (182 SCUs; `…:check` green). | check green locally. | fixed in `68a56814a`; **remote PASS confirmed** at `66d168174` |
| Unit Tests | `nirmana-analysis-receipts.test.ts` — layer aggregates re-derived from the live inventory mismatch the committed pins (L1 `b3674dfb…` vs committed `93de3b2c…`; L3 similarly). Same root cause as Governance Gates (ii). | NOT branch-local-fixable without authority — see 2c. | — | FAIL — remote log confirms exactly 3 failing assertions, all inside `nirmana-analysis-receipts.test.ts` (pinned receipt count; wrong-layer refusal; hand-edited-pin re-derivation) — the pins root cause only |

**Final remote state at HEAD `66d168174`: 32 pass / 15 skip / 2 fail** (`Governance Gates`
+ `Unit Tests`, both pins-only). `mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED`.
Note: `origin/main` advanced one commit past our merge (`fd4c3d4b1`, #2752) after the
readiness work began; PR checks run on `refs/pull/2731/merge` against current main, so
this does not invalidate the results above. Re-merging main again was NOT done — F-0's
merge authorization was scoped to the one conflict-resolution merge.

### 2c. RESOLVED (second pass) — nirmana layer-pins re-admission executed under D-E022

**Resolution:** the native issued **D-E022** (2026-09-29, recorded in pravaha
`EVENTS.jsonl`: "Accept all recommendations." — pins re-admission at the #2731 merge
authorised, per MERGE_HYGIENE_12_10c_RUNBOOK). Executed in A0.3:

- **Authority evidence:** `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_E022_PINS_READMISSION_AUTHORITY_v1_0.md`
  (introduced `442f1ed9`; identity-bound amendment `f4cba9d6`), registered in the generator's
  `AUTHORITY_BINDINGS["D-E022"]` + `AUTHORIZED_SOURCE_COMMITS["D-E022"]` (`ec98215b`).
- **Successors admitted** (`nirmana_analysis_layer_pins.py --admit-successor`, fail-closed,
  append-only; membership unchanged everywhere):
  - L1: `l1:f4cba9d606ab:b3674dfbfa91` (supersedes `l1:149f8479ac4e:93de3b2c84b7`; 6 assets:
    `ga_strength`/`ga_sensitive` `approved_intentional_change`, 4 `derived_import_change`).
  - L3 #1: `l3:f4cba9d606ab:64ca6e06c175` (supersedes `l3:7d40f8c70640:dfcf30d8b3d2`; 7 assets:
    5 `approved_intentional_and_derived_import_change`, 2 `derived_import_change`).
  - L3 #2: `l3:ad22bef06784:d1bf773c4d94` (supersedes L3 #1; 3 knots-closure writers,
    all `derived_import_change` — DP-SD-010 serialization cascade, §2.0 item 3).
- `--check --protected-baseline-commit 55ec5e355…` exit 0 locally; the CI Governance Gates
  pins step is green at `650846852`; `nirmana-analysis-receipts.test.ts` green.

First-pass stop-item text below kept for the record.

<details><summary>First-pass §2c (STOP ITEM, superseded)</summary>

Root cause, precisely: this branch's own writer edits since the pinned convergence
commits moved two layers' writer-inventory aggregates —

- **L1 (`ga_`)**: `1fab2364e` (WP8 G-10: `ga_strength_writer.py` +90, `ga_sensitive_writer.py`
  +21, `CHART_FACTS_SCHEMA.json` entry) and `ddf985751` (M-6). Committed pin
  `l1:149f8479ac4e:93de3b2c84b7`; live inventory derives `b3674dfbfa91…`.
- **L3 (`ka_`)**: this lane's gochara writer/kernel work since `7d40f8c70640`
  (`bb7644ee4`, `b70115631`, `4d8f83050`, `8b5d7f4ed`, `c2eb8a780`, `660e12129`,
  `3d606523b`, `8c8dd2a1f`, `fe3038be7`, `ac746434a`, `f1ee17c81`, `9ef81897c`,
  `3c7bf6947`, `45f150bb9`, …). Committed pin `l3:7d40f8c70640:dfcf30d8b3d2`; live
  inventory derives `64ca6e06c175…`.

Why the executor stopped: `--admit-successor` writes an **admission record** carrying
`authority_decision` / `authority_commit` / `review_artifacts` / per-asset
classifications. The only authority the 12.10c runbook names
(`NATIVE-2026-09-24-L0-REPAIR-REPIN`, commit `101171f76517`) is **scoped to the L0-repair
change set (PR #2727) and is already consumed** by the currently committed L0/L2/L3
generations — it does not authorize successors for THIS lane's different change set, and
it names **no L1 generation at all**. Writing either successor without a native decision
would fabricate the authority field — the exact defect class the gate exists to catch.
**Needed from the native: one authority decision covering the L1 (ga_, G-10/M-6 change
set) and L3 (ka_, this lane's writer change set) successor admissions** (or a ruling
extending an existing decision). The mechanics (read-only DB for receipt counts, command
per runbook §2) are staged and can run within minutes once authority exists.

Also noted: `nirmana-analysis-receipts.test.ts` (Unit Tests) fails on the same staleness;
it goes green when the pins do.

</details>

## 3. DEPLOY MIGRATION LIST — `migrate.ts --dry-run` against production

**Re-run 2026-09-29 second pass (HEAD `650846852`): would-apply set is unchanged —
exactly `{1071, 1072, 1086}`** (same method as below: fresh secret, own proxy on 55440,
role `amjis_app`, `--dry-run` only, proxy torn down after; only pre-existing DVA-RULING-73
disclosures emitted).

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

**SECOND PASS (2026-09-29, HEAD `650846852`): steps 1–3 ALL EXECUTED.**

- **Step 1 (writer digests):** `provenance_inventory --check` exit 0 at HEAD (regenerated
  once more in `ad22bef06` after the knots.py DP-SD-010 fix moved three digests).
- **Step 2 (pins re-admission):** EXECUTED under **D-E022** — §2c. Three successors
  (L1 ×1, L3 ×2), all append-only with per-asset classifications.
- **Step 3 (capability-estate census):** `codegen:capability-estate-census:check` green at
  HEAD (regenerated after each tree-moving commit in this pass).
- **Step 4 (1072 interplay):** recorded note, nothing to run.
- **Step 5 (commit):** fully applied across `442f1ed9`…`650846852`.

First-pass duty-assessment text below is kept for the record; its "pending native go"
recommendation was answered by D-E022.

<details><summary>First-pass §4 (superseded)</summary>

`MERGE_HYGIENE_12_10c_RUNBOOK.md` — documented 2026-09-27. **Execution state as of
2026-09-29 (this lane, on-branch, per the packet §4 duty assignment): step 1 EXECUTED
(writer digests regenerated, `--check` green), step 3 EXECUTED (census regenerated, check
green), step 2 STOPPED on missing native authority (§2c), step 4 is a recorded note,
step 5 partially applied (steps 1+3 committed in `bd5c34fb0`).** The runbook's own
"nothing may run before the second merge lands" constraint is satisfied differently than
written: the merge commit `f95cf19af` exists ON THIS BRANCH, so the merged tree it
requires is this tree.

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

</details>

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

## HEADLINE VERDICT: **READY, TWO NATIVE DECISIONS STANDING** (updated 2026-09-29 second pass, HEAD `650846852`)

**CI is fully green (1514 pass / 0 fail) and the PR is MERGEABLE/CLEAN.** First-pass stop
item 1 (pins re-admission authority) is **RESOLVED by D-E022** — §2c.

Stop items still standing, both native territory, both unchanged from first pass:

1. **STOP-LEVEL: deploy runner would apply 1071 + 1072 at merge** — intended? (1072 flips
   `target_table` and breaks conjunct (j) if applied uncoordinated; standing instruction is
   DO NOT apply locally.) Re-confirmed by second-pass dry-run (§3). Native decision required.
2. **OPEN native coordination: 1086** — the native must confirm with the L1 lane that
   applying it at deploy is intended. Not confirmable by this lane.

New non-blocking note from the second pass: no seed entry in `asset_registry_seed.ts`
currently owns `kala_gochara_windows` generation `'3.0'` — `ka_gochara` is ruled to
`_v2`/`'2.0'` only, and `ka_gochara_v3_century_materialize`'s seed entry targets `_v2` with
`generation LIKE 'g3_%'`. Whether the `'3.0'` surface needs a seed row (or is deliberately
migration-only) is a native/L3-plan question, not a merge blocker.

<details><summary>First-pass verdict (HOLDING, superseded)</summary>

Stop items, in order:

1. **Nirmana layer-pins re-admission (12.10c step 2) — NATIVE AUTHORITY REQUIRED** (§2c).
   Two checks stay red until it lands: `Governance Gates` (pins `--check`) and
   `Unit Tests` (`nirmana-analysis-receipts.test.ts`). Both fail ONLY on the L1+L3 pin
   staleness; everything else in those jobs is fixed and locally green.
2. **STOP-LEVEL: deploy runner would apply 1071 + 1072 at merge** — intended? (1072 flips
   `target_table` and breaks conjunct (j) if applied uncoordinated; standing instruction is
   DO NOT apply locally.) Native decision required.
3. **OPEN native coordination: 1086** — the native must confirm with the L1 lane that
   applying it at deploy is intended. Not confirmable by this lane.

Resolved in this pass (was stop item 1/2): D-01a, Secret Scan, Earned-Signal §N.8,
Fact-Category Pinning, Density Census, the provenance-inventory staleness, the drift and
schema_validator ceilings, and the SESSION_LOG CRITICAL — all fixed branch-local with
local-equivalent green evidence (§2b) and **remote PASS confirmed at `66d168174`** for
every one of them.

12.10c runbook execution state: **step 1 (writer digests) EXECUTED** on the merged tree —
`nirmana-writer-digests.json` regenerated, `--check` green; **step 3 (capability-estate
census) EXECUTED** — `capability_estate_census.json` regenerated
(`--source-revision=f512bdfe4`, the HEAD at generation time), check green; **step 2 (L3
pin re-admission) STOPPED** — §2c, native authority needed; step 4 (1072 interplay) is a
recorded note, nothing to run; step 5 (commit) partially applied (steps 1+3 outputs
committed in `bd5c34fb0`).

</details>

Non-blocking, recorded: Disclosure 3 (R240); chart-1 `'4.0'` burned; chart-2 candidate
retention; soak trigger #0 added to `step09_soak_checklist.md`; frozen seven + 1150 verified
absent from the deploy pending list.

Next native actions: rule on the two standing stop items; merge + deploy #2731; then
DEPLOY_SHA verification → Cloud-Run century rebuild → flips under trigger #0 + soaks
(ADK-0028 amended sequence).
