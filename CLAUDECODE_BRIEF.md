---
artifact: CLAUDECODE_BRIEF.md
canonical_id: CLAUDECODE_BRIEF
version: 4.1
status: COMPLETE
authored_by: Cowork (Claude Sonnet 4.6) 2026-05-21
authored_for_session: CV2-FINAL
purpose: >
  Final orchestrator for the Chat V2 governance close-out arc. Merges the three
  open governance PRs (#135, #136, #137) into main, executes operator gate B
  (Cloud Run R8 flags + Cloud Build + panchang bootstrap audit), resolves the
  HUMAN_GATE_D learning-layer frontmatter items, executes three drift-triage fix
  sessions (T.1–T.3), merges the four triage/governance PRs (#138–#141) via
  E.1–E.4 serial train, and cleans up the MadhavCV2Wrap worktree.
  Operates from `/Users/Dev/Vibe-Coding/Apps/Madhav` (main checkout).
# v4.1 changelog: added E.1–E.4 merge train (PRs #138–#141) + F.1 Chrome MCP smokes; updated execution_order + merge_policy

scope_note: >
  CV2-FINAL arc only. Does NOT touch M5 campaign branches, ICR branches,
  m6-prospective-testing, or Conductor branches. May_touch and must_not_touch
  declarations in §8/§9 below are binding for all packets and sub-agents.

# ════════════════════════════════════════════════════════════════════════════
# EXECUTION STATE — orchestrator updates this YAML after every packet
# ════════════════════════════════════════════════════════════════════════════
packet_status:
  M.1:  DONE           # merged PR #135 (session-log-structure) SHA cfee508b; CURRENT_STATE v5.32
  M.2:  DONE           # merged PR #137 (drift-high-triage) SHA e66626b3; CURRENT_STATE v5.33
  M.3:  DONE           # merged PR #136 (corpus-frontmatter) SHA 96f30bc3; CURRENT_STATE v5.34
  B.1:  DONE           # gcloud: flipped R8 flags; revision amjis-web-00289-jcn
  B.2:  SKIP_NO_CHROME_MCP   # browser smoke — Chrome MCP not connected
  B.3:  DONE           # CI/CD auto-deploy: "Deploy to Cloud Run" run 26228513324 succeeded (96f30bc3)
  B.4:  SKIP_NO_CHROME_MCP   # browser smoke — Chrome MCP not connected
  B.5:  DONE           # audit complete; gap documented in cv2final/B5_BOOTSTRAP_AUDIT.md; committed 819458ba
  D.1:  DONE           # SIGNAL_WEIGHT_CALIBRATION status→STUB; OBSERVATIONS delimiters+mechanism_id
  D.2:  DONE           # path_exclude added to artifact_schemas.yaml + schema_validator.py
  D.3:  DONE           # PR #138 opened — governance-hygiene/learning-layer-frontmatter
  T.1:  DONE           # PR #139 — gh-path-fix; MSR path+fingerprint_sha256 fixed
  T.2:  DONE           # PR #140 — gh-phantom-ref-fix; 6 phantom refs eliminated
  T.3:  DONE           # PR #141 opened — governance-hygiene/gh-fp-backfill; fingerprint backfill
  E.1:  DONE           # merged PR #138 commit bb4e7c11; CURRENT_STATE v5.38 (pre-populated by WRAPUP-S2)
  E.2:  DONE           # merged PR #139 commit a2a0012f
  E.3:  DONE           # merged PR #140 commit 91ede83b; 6 phantom refs eliminated
  E.4:  DONE           # merged PR #141 commit 35bc824f; ~119 fingerprints backfilled
  F.1:  SKIP_DEFERRED  # Chrome MCP unavailable (browser profile lock); F1_SMOKE_DEFERRED.md written
  C.1:  DONE           # MadhavCV2Wrap worktree already removed in prior session; cv2/wrapup-governance branch not found
  C.2:  DONE           # CV2_FINAL_SUMMARY.md written; CURRENT_STATE v5.39; SESSION_LOG appended; MP.2 mirror updated; brief COMPLETE

last_completed_packet: C.2
last_halt: null
session_resumed_count: 3

execution_order:
  - M.1
  - M.2
  - M.3
  - B.1
  - B.2
  - B.3
  - B.4
  - B.5
  - D.1
  - D.2
  - D.3
  - T.1
  - T.2
  - T.3
  - E.1
  - E.2
  - E.3
  - E.4
  - F.1
  - C.1
  - C.2

merge_policy:
  M.1: auto_merge            # PR was already reviewed; squash + delete branch
  M.2: auto_merge
  M.3: auto_merge
  D.3: open_pr_only          # governance trail PR — human review before merge
  T.1: open_pr_only          # path-fix PR
  T.2: open_pr_only          # phantom-ref PR
  T.3: open_pr_only          # fingerprint-backfill PR
  E.1: auto_merge_serial     # override: merge train — PR #138
  E.2: auto_merge_serial     # override: merge train — PR #139
  E.3: auto_merge_serial     # override: merge train — PR #140
  E.4: auto_merge_serial     # override: merge train — PR #141
---

# CV2-FINAL Orchestrator Brief

## §1 — Mission

Close the Chat V2 governance arc from `/Users/Dev/Vibe-Coding/Apps/Madhav` (main).
End state: all three governance PRs merged, R8 Cloud Run flags live, drift/schema
residuals documented, three triage-fix PRs opened for human review, MadhavCV2Wrap
worktree removed, final summary committed.

## §2 — Operating principles

- **Single checkout.** Everything executes in `/Users/Dev/Vibe-Coding/Apps/Madhav`.
  Per-packet branches are created, worked, pushed, and PRs opened — then HEAD
  returns to main.
- **State lives in packet_status.** Read it at session open; write it after each
  packet via `Edit` (never `Write`/overwrite).
- **Halt protocol.** On any ambiguous outcome write
  `00_ARCHITECTURE/CONDUCTOR/cv2final/HUMAN_GATE_<packet>.md` with reason +
  next-action, set `last_halt`, STOP.
- **No git add -A.** Always stage specific files by name. `git add -A` is banned —
  it risks absorbing untracked orchestration files into branch commits.
- **Co-Authored-By trailer** on every commit:
  `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

## §3 — Packet ledger

| Packet | Title | Operation | Outcome |
|---|---|---|---|
| M.1 | Merge PR #135 | rebase + squash merge | DONE |
| M.2 | Merge PR #137 | rebase + squash merge | DONE |
| M.3 | Merge PR #136 | rebase + squash merge | DONE |
| B.1 | R8 Cloud Run flags | gcloud update amjis-web | flags live |
| B.2 | Browser smoke R8 | Chrome MCP | SKIP |
| B.3 | Cloud Build | gcloud builds submit | build green |
| B.4 | Browser smoke scroll/validator | Chrome MCP | SKIP |
| B.5 | bootstrap_panchanga.py audit | read + document gap | findings committed |
| D.1 | Learning-layer frontmatter | fix 2 named files | files fixed |
| D.2 | schema_validator path_exclude | patch validator + schema | patch committed |
| D.3 | Governance trail | branch + PR | PR open |
| T.1 | MSR path fix | patch CAPABILITY_MANIFEST | PR open |
| T.2 | Phantom ref removal | patch CAPABILITY_MANIFEST | PR open |
| T.3 | FP backfill | compute + patch manifest | PR open |
| C.1 | Worktree cleanup | remove MadhavCV2Wrap worktree | worktree removed |
| C.2 | Final summary | write + commit + push | brief COMPLETE |

## §4 — Per-packet execution recipes

### Packets M.1–M.3 — DONE (see packet_status)

Merges completed:
- M.1: PR #135 → cfee508b; CURRENT_STATE v5.32
- M.2: PR #137 → e66626b3; CURRENT_STATE v5.33
- M.3: PR #136 → 96f30bc3; CURRENT_STATE v5.34

### Packet B.1 — R8 Cloud Run flags

**Action — orchestrator-side:**
```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R8_SLASH_ENABLED=true,MARSYS_FLAG_R8_EXPORT_ENABLED=true,MARSYS_FLAG_R8_TOKENS_ENABLED=true
```
Verify: `gcloud run services describe amjis-web --region asia-south1 --format='value(spec.template.spec.containers[0].env)'`
Flip B.1 to DONE. Continue to B.2.

### Packet B.2 — SKIP (Chrome MCP not connected)

### Packet B.3 — Cloud Build

**Action — orchestrator-side:**
```bash
gcloud builds submit --config=platform/cloudbuild.yaml platform/
```
Wait for build to complete. If exit non-zero, write HUMAN_GATE_B3.md and HALT.
On success flip B.3 to DONE. Continue to B.4.

### Packet B.4 — SKIP (Chrome MCP not connected)

### Packet B.5 — bootstrap_panchanga.py audit

**Action — orchestrator-side:**
1. Read `platform/scripts/bootstrap_panchanga.py` (or its actual path — find with
   `find platform -name "bootstrap_panchanga.py"`).
2. Check: does the script auto-register a `build_manifests` row for each run?
3. Write findings to `00_ARCHITECTURE/CONDUCTOR/cv2final/B5_BOOTSTRAP_AUDIT.md`.
4. Commit the findings file to main with message:
   `docs(governance): B.5 bootstrap_panchanga.py build_manifests auto-registration audit`
5. Flip B.5 to DONE.

### Packet D.1 — Learning-layer frontmatter (HUMAN_GATE_D items)

**Context:** HUMAN_GATE_D.md documents two files that the corpus-frontmatter
sub-agent couldn't fix without native arbitration:
1. `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/README.md` — change
   `status: ACTIVE-PENDING` to `status: STUB`.
2. `06_LEARNING_LAYER/OBSERVATIONS/README.md` — add `---` frontmatter delimiters
   around the existing YAML preamble so schema_validator can parse it.

**Action:**
1. Create branch: `git checkout -b governance-hygiene/learning-layer-frontmatter origin/main`
2. Apply the two file edits (specific fields only — do NOT alter content outside frontmatter).
3. Run `python3 platform/scripts/governance/schema_validator.py 2>&1 | head -40` to verify
   the two files no longer produce violations.
4. Stage specific files: `git add 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/README.md 06_LEARNING_LAYER/OBSERVATIONS/README.md`
5. Commit + push. Open PR.
6. Return to main. Flip D.1 to DONE. Continue to D.2.

**Halt condition:** If either file has unexpected structure that makes a safe edit
ambiguous, write HUMAN_GATE_D1.md and halt.

### Packet D.2 — schema_validator path_exclude

**Context:** `artifact_schemas.yaml` `learning_layer_stub` class needs a
`path_exclude` field so the validator can skip certain learning-layer paths. Then
`schema_validator.py` must honor `path_exclude` during validation.

**Action:**
1. On the same branch as D.1 (or a new one if D.1 already pushed):
   `git checkout -b governance-hygiene/learning-layer-frontmatter` (if not already on it)
2. Read `platform/scripts/governance/schemas/artifact_schemas.yaml` — find the
   `learning_layer_stub` class definition.
3. Add `path_exclude: []` field (a list of glob patterns to skip). Do NOT add any
   actual patterns unless the schema already documents them — just the empty list as
   the extensibility point.
4. Read `platform/scripts/governance/schema_validator.py` — find where
   `learning_layer_stub` checks are applied; add logic to skip files matching any
   `path_exclude` pattern.
5. Run validator to verify exit code does not regress vs. current baseline (exit ≤ 2).
6. Stage specific files and amend/add to the D.1 branch commit, or a new commit.
7. Flip D.2 to DONE. Continue to D.3.

**Constraint:** Do NOT widen any other schema class. Do NOT change required fields
for any class. Only add `path_exclude` to `learning_layer_stub`.

### Packet D.3 — Governance trail commit + PR

**Action:**
1. On branch `governance-hygiene/learning-layer-frontmatter` (or same branch as
   D.1/D.2):
2. Update CURRENT_STATE_v1_0.md: bump to v5.35, document D.1/D.2 changes.
3. Append SESSION_LOG entry.
4. Update .gemini/project_state.md (MP.2 mirror).
5. Stage + commit:
   `git add 00_ARCHITECTURE/CURRENT_STATE_v1_0.md 00_ARCHITECTURE/SESSION_LOG.md .gemini/project_state.md`
6. Push. Open PR with `gh pr create`. Do NOT merge.
7. Return to main. Flip D.3 to DONE. Continue to T.1.

**merge_policy: open_pr_only** — PR #138 expected.

### Packet T.1 — MSR canonical path disagreement

**Context:** Drift triage REPORT.md (H.3.1 finding) identified 1 MSR path
disagreement in CAPABILITY_MANIFEST.json. The manifest entry for MSR lists a
stale or incorrect canonical path.

**Action:**
1. Read `00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/REPORT.md`
   to get the exact H.3.1 finding (file path, expected vs. actual).
2. Create branch: `git checkout -b governance-hygiene/gh-path-fix origin/main`
3. Edit `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — fix the MSR path entry only.
4. Run `python3 platform/scripts/governance/drift_detector.py 2>&1 | grep "H.3.1"` to
   verify the finding resolves.
5. Commit with `git add 00_ARCHITECTURE/CAPABILITY_MANIFEST.json`.
6. Push. Open PR. Do NOT merge.
7. Return to main. Flip T.1 to DONE.

**merge_policy: open_pr_only**

### Packet T.2 — Remove 6 phantom ref entries

**Context:** H.3.7 found 6 phantom ref entries in CAPABILITY_MANIFEST.json —
entries that reference files/paths that do not exist on disk.

**Action:**
1. Read `00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/REPORT.md`
   to get the exact 6 H.3.7 entries.
2. Create branch: `git checkout -b governance-hygiene/gh-phantom-ref-fix origin/main`
3. Edit `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — remove the 6 phantom entries.
4. Run `python3 platform/scripts/governance/drift_detector.py 2>&1 | grep "H.3.7"` to
   verify the 6 findings are gone.
5. Commit specific file. Push. Open PR. Do NOT merge.
6. Return to main. Flip T.2 to DONE.

**merge_policy: open_pr_only**

### Packet T.3 — SHA256 fingerprint backfill

**Context:** H.3.2 found 80 entries with blank-declared or stale fingerprints.
Subcategories from REPORT.md: 13 stale real-hash, 37 PENDING_CI_REGENERATION,
29 blank-declared, 1 PENDING_4C_2.

**Action:**
1. Create branch: `git checkout -b governance-hygiene/gh-fp-backfill origin/main`
2. For each of the 80 entries identified in REPORT.md:
   - If the file exists on disk: compute `sha256sum <path>` and write the hash.
   - If the file is PENDING_CI_REGENERATION or does not exist: leave as
     `PENDING_CI_REGENERATION` (document in commit message).
   - If PENDING_4C_2: leave as-is with a comment in commit message.
3. This is high-volume work — dispatch as sub-agent.
4. Verify: `python3 platform/scripts/governance/drift_detector.py` exit code
   should not increase vs. baseline; H.3.2 blank-declared count should drop.
5. Commit `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` only. Push. Open PR.
6. Return to main. Flip T.3 to DONE.

**merge_policy: open_pr_only**

**Sub-agent guidance:** This packet is high-volume but mechanical. Dispatch a
`general-purpose` sub-agent from `/Users/Dev/Vibe-Coding/Apps/Madhav` with the
REPORT.md path, the list of 80 entries, and instructions to: (a) read each file
path from the manifest, (b) compute sha256 where file exists, (c) write updated
JSON, (d) never use `git add -A`, (e) report count of hashes computed vs. left
as PENDING.

### Packet C.1 — Remove MadhavCV2Wrap worktree

**Action — orchestrator-side:**
1. Verify `cv2/wrapup-governance` branch has no uncommitted work:
   `git -C /Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap status`
2. Remove the worktree:
   `git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap`
3. Prune: `git worktree prune`
4. Delete remote branch (it was a local-only tracking branch):
   `git branch -d cv2/wrapup-governance 2>/dev/null; git push origin --delete cv2/wrapup-governance 2>/dev/null || true`
5. Verify: `git worktree list` — MadhavCV2Wrap should be gone.
6. Flip C.1 to DONE.

**Halt condition:** If `git worktree remove` fails because the worktree has
modifications or a rebase in progress, write HUMAN_GATE_C1.md and halt.

### Packet C.2 — Final summary + brief COMPLETE

**Action — orchestrator-side:**
1. Run validator triple:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/Madhav
   python3 platform/scripts/governance/schema_validator.py 2>&1 | tail -5; echo "schema exit: $?"
   python3 platform/scripts/governance/drift_detector.py 2>&1 | tail -5; echo "drift exit: $?"
   python3 platform/scripts/governance/mirror_enforcer.py 2>&1 | tail -5; echo "mirror exit: $?"
   ```
2. Write `00_ARCHITECTURE/CONDUCTOR/cv2final/CV2_FINAL_SUMMARY.md` with:
   - All 16 packets: final status (DONE | SKIP | PR_OPEN | HALTED | DEFERRED).
   - PR URLs for T.1/T.2/T.3/D.3 (still open, awaiting human merge).
   - Validator triple final exit codes.
   - Open operator actions (B.1 verified, B.3 build SHA, B.2/B.4 skipped).
   - Deferred items (any T.N packets left as PENDING).
3. Flip this brief's `status:` to `COMPLETE` and `last_completed_packet: C.2`.
4. Commit to main:
   ```bash
   git add 00_ARCHITECTURE/CONDUCTOR/cv2final/CV2_FINAL_SUMMARY.md CLAUDECODE_BRIEF.md
   git commit -m "docs(cv2-final): final summary + brief COMPLETE

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   git push origin main
   ```
5. Emit terminal chat message (§5 below).

## §5 — Terminal message format

After C.2:

```
CV2-FINAL orchestrator complete.

Packet statuses: [list all 16]

PRs awaiting human review:
  - D.3: PR #138 — governance/learning-layer-frontmatter
  - T.1: PR #N — gh-path-fix
  - T.2: PR #N — gh-phantom-ref-fix
  - T.3: PR #N — gh-fp-backfill

Operator: B.1 (R8 flags), B.3 (Cloud Build) — verify in Cloud Run / Cloud Build console.
B.2 + B.4 skipped (Chrome MCP unavailable).

Deferred: [any T.N left pending]

DONE.
```

## §6 — Resumability protocol

On launch (initial OR resume):
1. Read `packet_status`. Increment `session_resumed_count`.
2. If `last_halt` non-null: check halt file → retry if transient, halt again if not.
3. Walk `execution_order`, find first non-terminal packet, execute it.
4. Update state after each packet completes.
5. Continue until all packets terminal or a halt.

## §7 — Halt-on-doubt clauses (sticky)

MUST halt if:
- A merge conflict touches a file not in the per-packet expected list.
- Validator suite regresses vs. baseline (drift exit >3 or schema exit >2).
- `git checkout <branch>` fails due to another worktree checkout.
- Sub-agent claims success but verification contradicts.
- Any unexpected error in `gcloud` commands.

## §8 — May touch

- `CLAUDECODE_BRIEF.md` (frontmatter state only)
- `00_ARCHITECTURE/CONDUCTOR/cv2final/**`
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (version bump only)
- `00_ARCHITECTURE/SESSION_LOG.md` (append only)
- `.gemini/project_state.md` (MP.2 mirror, adapted parity)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (T.1/T.2/T.3 only — specific entries)
- `platform/scripts/governance/schemas/artifact_schemas.yaml` (D.2 — path_exclude only)
- `platform/scripts/governance/schema_validator.py` (D.2 — path_exclude honor logic only)
- `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/README.md` (D.1 — status field only)
- `06_LEARNING_LAYER/OBSERVATIONS/README.md` (D.1 — frontmatter delimiters only)

## §9 — Must NOT touch

- `platform/src/**`
- `01_FACTS_LAYER/**` (except what D.1 brief explicitly names)
- `025_HOLISTIC_SYNTHESIS/**`
- `06_LEARNING_LAYER/**` (except D.1 two named files)
- `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md`
- `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml`
- Any M5/ICR/m6/conductor branch files
- `.geminirules` (no structural change — only D.3 mirror update if MP.1 triggered)
- `.env.local` or any secrets file
- Financial transaction tables or DB migrations
