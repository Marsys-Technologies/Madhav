---
artifact: PURNA_ANVESANA_PREPARATION_MANIFEST
version: 1.0
status: PREPARATION_COMPLETE_SOURCE_EXECUTION_NOT_AUTHORIZED
date: 2026-09-27
authority: Native authorization for preparation only
execution_authorized: false
deployment_authorized: false
---

# Pūrṇa Anveṣaṇa — preparation and preservation manifest

## 1. Purpose and boundary

This record proves that the stopped Pūrṇa Anveṣaṇa campaign can be resumed without using a shared
checkout and without losing the unmerged, uncommitted, historical, or private evidence discovered
during the stocktake. It authorizes no source implementation, PR mutation, merge, migration,
database write, deployment, live collection, or campaign-completion claim.

The future executor is Anthropic Claude Code. Its primary checkout is the dedicated worktree below.
Every older worktree and branch is a read-only salvage source until a reviewed packet explicitly
selects content for semantic reimplementation.

## 2. Exact resumption workspace

| Field | Frozen value |
|---|---|
| Worktree | `/Users/Dev/.codex/worktrees/purna-anvesana-resumption-v2/Madhav` |
| Branch | `codex/purna-anvesana-resumption-v2` |
| Base | `origin/main` |
| Base/head SHA | `6b26f3ff05ee0aba3cdd964bce62292496ae6b62` |
| Base freshness check | fetched `origin/main` on 2026-09-27; `HEAD...origin/main = 0/0` |
| Worktree state at creation | clean |
| Shared root permitted use | read-only inspection only |

The worktree was created through the managed worktree service. The first attempt without an
explicit ref failed because the remote default could not be inferred; the successful creation was
explicitly pinned to `origin/main`. No source work was started.

## 3. Content-addressed preservation set

The preservation root is outside every Git worktree:

`/Users/Dev/madhav-purna/preservation/2026-09-27-preparation-v1`

| Item | SHA-256 | Meaning |
|---|---|---|
| `purna-relevant-refs.bundle` | `5d5c171ed8dec554a5fbe23bf571d6cb9ee4559b7edf62018340ad0f36717823` | Complete histories for main and the principal candidate/residual refs |
| `dirty/purna-focused-completion/2026-09-17-purna-anvesana-focused-completion.md` | `023bc0705819a92b8b2cf9605b57f9d87ef7fcc9e9c17065393d45af4d062f88` | Untracked historical focused-completion plan |
| `dirty/purna-wealth-near-miss/register_d9_judgment.integration.test.ts` | `31d2a8d02cc6ea7cf08e9a0967b86e0d71e65bc63837245cd416d0db8b331e27` | Modified unfinished integration test |
| `dirty/purna-wealth-near-miss/register_d9_judgment.near_miss_contract.test.ts` | `445b044db87e366a418f640086ba2f4de2ee24ebba345463b65b67c2abdb800f` | Untracked red-first near-miss test |
| `dirty/purna-wealth-near-miss/tracked.patch` | `d03572dfb3b15fd8fb123039050d3a7dbb13114c371be11ae5f41dca61e54468` | Replayable tracked diff |
| `strategy/PURNA_ANVESANA_CLAUDE_CODE_RESUMPTION_STRATEGY_v1_0.md` | `a047e3c02e5f1ab916e5390defe6bd8ba4f8be795aeba78dfd05b6299ac69061` | Approved preparation/resumption strategy |
| `strategy/PURNA_ANVESANA_INDEPENDENT_REVIEW_v1_0.md` | `43fad76b866d4e6ff10ed40b17e22845fbe8ec2facd3aa9589fcb6dbf7934d31` | Independent diagnosis and elevated plan |
| `strategy/PURNA_ANVESANA_INDEPENDENT_REVIEW_HANDOFF_v1_0.md` | `84439ed4c8807498fc4814dbf5aef13c0dabdd91b7e33218ca0854e3d11805f8` | Full campaign lineage and review handoff |
| `task-history/rollout-2026-09-19T09-37-01-01a0b7d8-9a90-74f3-aab9-80014919f8b2.jsonl` | `671c564766c22c413406b3db8f5e5cb692458e4b29db14c315dcfb95e7862c7c` | Original Product Completion II task transcript |

The Git bundle was verified as valid and complete. The tracked patch was verified with
`git apply --check` against a disposable archive of candidate head `34991645b1d57926d97ac027d6fca59d8c2ecb53`.

The bundle preserves complete histories for:

- `origin/main` at `6b26f3ff05ee0aba3cdd964bce62292496ae6b62`;
- PR #2705 candidate at `34991645b1d57926d97ac027d6fca59d8c2ecb53`;
- PR #2704 correction at `889ceaf9b7bb37e3699c921589498289d2e5aee5`;
- product-completion v3 at `fa8f6d5b235c17deda2091c18c3c00fc6a0bf9a5`;
- owner-usage allowlist at `4801150687dbd243004cdbf4730ce1b30d41570a`;
- focused-completion at `dcb303a671636fcf2ba56ba76ae7866e081c33c7`.

## 4. Restricted historical live evidence

Historical live artifacts were copied without inspecting or reproducing their raw payload into:

`/Users/Dev/Madhav-Private/purna-anvesana/2026-09-20-live-evidence`

The directory is owner-only (`0700` at its protected parent; files `0600`). It contains:

| Item | Size | SHA-256 |
|---|---:|---|
| `live-config-20260920.json` | 485 bytes | `3d27e427424522102c1408a9c1a9cea0f987527354795c5c70578c8f49e37cd6` |
| `live-20260920/collection-2026-09-19T21-14-50-807Z.json` | 1,132,761 bytes | `2a03b4a75667fff732e319d7e8219712b4ac8a680c1f0688c7a5276edcd01462` |

These files are historical evidence, not an active configuration, current authorization, or
permission to rerun a collection. They must never be committed or attached to a PR.

## 5. Original surfaces left untouched

| Surface | Preserved state | Rule |
|---|---|---|
| `/Users/Dev/.codex/worktrees/purna-wealth-near-miss/Madhav` | branch #2705 plus one modified and one untracked test | read-only; do not clean, rebase, or commit |
| `/Users/Dev/.codex/worktrees/purna-focused-completion` | one untracked plan | read-only; do not clean |
| `/Users/Dev/.codex/worktrees/0ee2/Madhav` | detached product-strategy checkout; resumption strategy untracked | read-only after preservation |
| `/Users/Dev/Vibe-Coding/Apps/Madhav` | heavily dirty shared campaign root | never a build surface |
| Original task `01a0b7d8-9a90-74f3-aab9-80014919f8b2` | stopped/idle historical executor | do not resume for source work |

No old worktree was cleaned, archived, rebased, switched, or removed. No PR was edited.

## 6. Current remote identities, refreshed 2026-09-27

| PR | Current identity | Disposition during preparation |
|---|---|---|
| #2705 | OPEN; `codex/purna-wealth-near-miss` → `main`; head `34991645b1d57926d97ac027d6fca59d8c2ecb53`; conflicting/dirty; old Unit Tests and Fact-Category Pinning failures | salvage library only; do not rebase wholesale |
| #2704 | OPEN; `codex/purna-pr2695-golden-alignment` → `codex/madhav-l3-claude-code`; head `889ceaf9b7bb37e3699c921589498289d2e5aee5`; mergeable/clean with no checks | remains L3-owned; not a #2705 dependency |

## 7. Verification and recovery

Current-base preparation checks completed on 2026-09-27:

- dependency install completed from the committed lockfile; no package file changed;
- focused Pūrṇa baseline: 7 test files, 6 passed and 1 skipped; 137 tests passed and 22 skipped;
- capability-knowledge codegen freshness passed: 182 SCUs, snapshot
  `sha256:0a2a675d0098390453d77ba0119b87fad865728e908290eaee6cc84fc465bc36`;
- capability-estate census freshness passed:
  `bb1de78236810ab9c17e547dd156ccbc6be87e99ffa9440f45aad46db966f113`;
- repository diff whitespace check passed.

The focused baseline covered overlay selection, dasha pagination/fencing, judgment fencing and
integration, inquiry compilation, response accountability, and planner outcome behavior. It is a
preparation baseline, not proof that the independent-review defects are fixed and not product
acceptance. The dependency installer reported upstream package vulnerabilities; none was changed or
suppressed because dependency remediation is outside this preparation scope.

Preparation is reproducible when all of the following hold:

1. the resumption worktree is on the exact branch and base above;
2. the bundle verifies and exposes every listed ref;
3. each preserved file matches its recorded SHA-256;
4. the candidate patch passes `git apply --check` against candidate head;
5. both old dirty worktrees retain their original dirty state;
6. the private evidence remains outside the repository and owner-only;
7. no platform source, migration, PR, database, or deployment changed.

If the new worktree is damaged before source execution begins, recreate it from the frozen base and
reapply only this preparation commit. Do not recover by moving or cleaning an old worktree.

## 8. Preparation exit state

Preparation is complete when this manifest, the salvage matrix, architecture addendum, reviewed
strategy/review corpus, and dormant Claude Code kickoff brief are committed locally on the dedicated
branch. The next gate is a separate Native authorization for source execution.
