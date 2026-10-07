# REVIEW PACKET — KĀLA-YANTRA execution design (charter, swarm, fleet, control plane, kickoff)

You are Astra, the independent reviewer of record for the Madhav project's Kāla work. Review the **execution design** of the KĀLA-YANTRA campaign before it is launched. Your standard: *will this campaign, run exactly as written by non-interactive Codex agents with no human in the loop, deliver the five lines of the charter's §0 without fail — and if not, what precisely breaks first?* You are read-only. You may not run builds, write files, or touch any database. You may read any file under the working root (a git worktree of the Madhav repo on branch `campaign/kalayantra`) and under the sibling worktrees named below.

## The native's priorities (verbatim, 2026-10-06)

"successfully implemented without fail … in a different work tree so that it does not impact the other work … high throughput, running in parallel wherever possible and sequentially wherever essential … optimise the entire development and CI/CD deployment … cut the governance and security-related overwork to only the essential and minimal … fully autonomous … a complete agentic swarm … The Gochara 5 has been mostly implemented, if not completely. It should be fully absorbed. We should not lose that work. There should be no human gates, no approval from humans. Have an owner surrogate … without digressions, without idle time, with high throughput, targeting the completion of all the assets and the campaign."

## What to read (all paths relative to the working root unless absolute)

**The design under review (every line is in scope):**
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md`
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md`
- `00_ARCHITECTURE/briefs/kalayantra/prompts/{SUTRADHARA,ADHIKARIN,PARIKSAKA,KARAKA}.md`
- `00_ARCHITECTURE/briefs/kalayantra/fleet/{kalayantra_fleet.sh,install_tracker.sh,preflight.sh,precheck.sh,local_db.sh,env.example.sh}`
- `00_ARCHITECTURE/control/kalayantra/plan_model.json`
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_KICKOFF_PROMPT_v1_0.md`

**What it must deliver (do not re-review these; they were reviewed and reconciled today — use them as the specification):**
- `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md` (§9 is the packet order the plan model encodes; §4.4, §6.2, §7 are the contracts)
- `00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md`
- `00_ARCHITECTURE/briefs/l3_families/decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md`
- `00_ARCHITECTURE/briefs/l3_families/reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md`

**Precedents and facts the design leans on (verify the design against them):**
- `00_ARCHITECTURE/briefs/nirmana/sessions/supervisor/CYCLE_CONTRACT_C8_V23.md` and `run_fleet.sh` (the supervised-cycle pattern being ported from Claude to Codex)
- `00_ARCHITECTURE/autonomy/CHARTER.md` (Nirmāṇa's ADHIKĀRIN) and `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_OWNER_SURROGATE_CHARTER_v1_0.md` (an accepted owner-surrogate form)
- The Pravāha campaign being absorbed, in the sibling worktree `/Users/Dev/madhav-l3/pravaha/`: `00_ARCHITECTURE/briefs/pravaha/PRAVAHA_CAMPAIGN_PLAN_v1_0.md`, `PRAVAHA_EXECUTION_ARCHITECTURE_v1_0.md`, `runbooks/SMALL_TEST_SITTING_CHECKLIST_v1_0.md`, `decisions/MEASURING_BUILD_CONTRACT_v1_0.md`, `decisions/NATIVE_RULINGS_BY_DELEGATE_v1_0.md`, `00_ARCHITECTURE/control/pravaha/plan_model.json`, and the tracker code `platform/scripts/governance/pravaha_tracker/{cli.py,server.py,state.py,detectors.py,runner.py}` (the design runs a second instance of this tracker via env overrides and copies the package to `main` with one generalisation)
- `.github/workflows/ci.yml` (triggers lines 15–90: `pull_request` allowlist is `main` + two historical integration branches; `merge_group`), `.github/workflows/deploy.yml` (triggers), `platform/scripts/governance/{secret_scan.sh,drift_detector.py,schema_validator.py,ci_changes.py}`
- `platform/python-sidecar/pipeline/orchestrator/{asset_runner.py,main.py,writers/__init__.py}` (frozen; the campaign must not touch them), `platform/scripts/dispatch_v5_small_test_job.py`, `platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py`
- `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` (the cross-campaign lease), `CLAUDE.md §N.2–§N.8`, the root `CLAUDECODE_BRIEF.md` (another workstream's active brief; the charter says it does not govern this fleet)

**Facts established by the author today (treat as given unless you find contrary evidence in the files):** branch ruleset 20141220 on `main` = required checks {TypeScript (src only), Unit Tests, Secret Scan (unit 0b.2), Governance Gates (…), TAP-6 — Method audit grep set, Governance Tool Tests (pytest)} + pull_request with `required_approving_review_count: 0` + merge queue (SQUASH, ALLGREEN, max 5 entries, 1 merge at a time) + non-fast-forward + no deletion; a CI run on `main` takes 9–13 minutes; `pravaha_tracker` is **not** on `origin/main` (only on `campaign/pravaha`); its CLI reads `PRAVAHA_HOME/EVENTS/PLAN_MODEL/TRACKER_PORT/URL/REPO/PGENV` from the environment but hard-codes `--to A|B|C` in `send` (cli.py:279) and refuses cross-stream item moves; `codex exec` 0.155.1 supports `-C`, `--dangerously-bypass-approvals-and-sandbox`, `-m`, `-c key=value`, `-o`, `--skip-git-repo-check`, reading the prompt from stdin; `NIRMANA_HOLD` exists at the Madhav root (that fleet is paused); 100 open PRs, 35 of them `pravaha/*` drafts; Pravāha tracker reads 75/102 done; `gcloud` is authenticated for project `madhav-astrology`; `DATABASE_URL` is not set in the author's shell; Docker 29 is present; the Python venv has pytest/psycopg/pyswisseph; the ephemeris files are pinned by sha256 in `ephemeris_pins.py` and downloadable from `https://storage.googleapis.com/madhav-ephemeris/se1/`.

## Questions (answer every one; cite file:line for every claim about a file)

**A. Will the fleet actually run?**
A1. Walk `kalayantra_fleet.sh` line by line as bash: find every bug (quoting, arithmetic, `wait` semantics with a subshell, `env` array expansion, `grep -c` returning non-zero on zero matches under `set -u` without `set -e`, the cycle counter, the watchdog, `nohup` of `$0`, macOS `date -r`). State which bugs stop the fleet, which corrupt accounting, which are cosmetic.
A2. Is a fresh `codex exec` session per cycle with the role prompt + charter the right trade against `resume`? What orientation cost per cycle do you estimate, and is the §5 orientation set sufficient for a worker to implement a K-packet item correctly without reading the whole plan each time?
A3. Will `--dangerously-bypass-approvals-and-sandbox` plus the charter's prohibitions be enough to keep agents from touching other campaigns' worktrees, `main`, or credentials — or is a mechanical guard needed (e.g. a git pre-push hook per worktree, a `PATH` shim)? Propose the smallest mechanical guards that remove the largest risks.
A4. The credential path (§7): `KY_BUILDER_DATABASE_URL` injected as `DATABASE_URL` into one lane for one armed cycle. Find the leak paths (log capture, `-o` last message, `env` in a tool output, the tracker's event detail). What exactly must the supervisor and the prompts do to make a leak impossible rather than discouraged?

**B. Will the control plane work?**
B1. Can the Pravāha tracker run as a second instance with only the env overrides listed in `install_tracker.sh`? Read `server.py`, `cli.py`, `state.py`, `detectors.py` and name every hard-coded path, port, stream list or assumption that breaks a second instance or the `S,N,V,K` streams. Is the proposed one generalisation (stream ids from the plan model) sufficient and correctly scoped?
B2. The pool design: six `K` workers under one stream id `K`. Does `cli.py start` actually refuse a second claim on a RUNNING item? Does `next` return only READY items whose `depends_on` are done? Does `done` require the owner stream? Is the verdict-by-message protocol (PARĪKṢAKA `send --to K --ref <ID>`) expressible with the current CLI, and will the tracker show it on the item? What breaks if two workers run `next` within the same second?
B3. Validate `plan_model.json` against the tracker's actual schema expectations (`state.py`): are `done_by`, `decision`, `steps`, `detector` shapes right; do the `db_query` detectors have plausible SQL given the real `kala_gochara_publication` schema (read the migration that creates it: search `platform/supabase/migrations` for `kala_gochara_publication`); do the `branch_merged` refs match the branch-naming rule; is any item unreachable (dependency never satisfiable), and is the DAG consistent with plan §9's order (name every deviation)?
B4. Decision items with `done_by: decision`: how does the tracker mark a decision decided (`cli.py decide`), and does `--as steward --delegated` work for stream `N`? Is anything in the model expecting a `native` actor that no longer exists?

**C. Is the Gochara 5.0 absorption complete and safe?**
C1. From the Pravāha plan model and tracker state, list what remains for `'5.0'` to flip (items, decisions, open PRs). Does the J lane (J-1…J-8, D-TEARDOWN, D-G9, D-CLOUD, D-FLIP, D-T2) cover all of it? What is missing or mis-ordered? Does anything in the K lanes risk overwriting or conflicting with Pravāha's open PRs (same files)?
C2. The G6 preconditions for `D-FLIP`: are they the right ones per the Pravāha plan, the evaluation protocol and the small-test checklist? Is anything there that a surrogate could not verify without a human (and if so, what detector replaces the human)?
C3. The steward hand-over (B-5, KYD-6): is running the J items through the Pravāha CLI as streams A/B sound, given `runner.py`'s stream config and the tracker's stream validators? Any state in `/Users/Dev/pravaha/run` the hand-over must respect?

**D. Throughput, CI/CD and isolation**
D1. Lane PRs target `main` directly through the merge queue. Given 9–13-minute CI, a 5-entry queue, 1 merge at a time, up to 6 workers plus the J lane landing ~35 existing PRs: what is the realistic landing rate, where will lanes idle, and what pacing rule should SŪTRADHĀRA apply? Would an integration branch (with a one-line `ci.yml` allowlist addition) beat direct-to-main for this workload, or is the author right to avoid it?
D2. `precheck.sh`: is it a faithful local proxy for the six required checks (compare with `ci.yml`/`tap-ci.yml` jobs), and will it run in under ~10 minutes on a laptop? Name what it misses and what it over-runs.
D3. Every merge to `main` deploys to Cloud Run. Which K-packet items ship migrations or writer changes whose deploy could break the live product before the layer is rebuilt, and what does the design do about it (candidate/published separation; additive migrations)? Name any item that is not deploy-safe as sequenced.
D4. Isolation: can anything the fleet does affect the Madhav main checkout, the `madhav-l3/*` worktrees, the Nirmāṇa fleet (paused), Suvarṇa's HELD PRs, or the Pūrṇa-Anveṣaṇa brief — through shared git metadata (`git worktree add` from the main checkout), the shared stash, the coordination branch, launchd labels, ports, or Docker names?

**E. Governance minimum**
E1. Is the §8 seven-rule minimum sufficient to satisfy CLAUDE.md §N.2–§N.8 and the hygiene policies the repository's CI enforces? Name any repository rule that will bite the fleet because it was cut (e.g. SESSION_LOG completeness, drift detector expectations, declaration validators, migration guards, the `ci_changes.py` docs-only classification).
E2. Is the campaign-level single SESSION_OPEN/SESSION_CLOSE defensible under `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`? What exactly must B-4 contain for `schema_validator.py --handshake` to pass (read the validator)?
E3. Is anything in the surrogate charter's granted powers something the native would plausibly NOT have intended to delegate given the verbatim directive — or anything reserved that the directive clearly delegates?

**F. The plan model itself**
F1. Is 80 items the right grain? Which items are too large for a 90-minute cycle (they will be killed by the watchdog repeatedly) and should be split into steps-as-PRs or sub-items? Which are too small?
F2. The value checkpoint (VC-1..3, D-VC) as sequenced before K5: does it genuinely test the model the plan says (G1), and is `D-VC`'s rubric the one the Kṣetra ruling sheet (ruling 10) and `NR-KALA-R12` fixed?
F3. What is missing from the model entirely (an item the §0 definition of done requires but no item produces)?

**G. Kickoff**
G1. Walk the kickoff prompt as the Codex session would execute it. Which step fails, in what order, and why (missing dirs, missing CLI, the tracker not yet on main, `ky` streams, `gh pr create` from a branch whose PR already exists, launching the fleet before B-1 merges)? Rewrite any step that must change.
G2. What should the operator see after a successful kickoff, and what single check tells them the fleet is alive and productive the next morning?

## Output

Write one Markdown document with frontmatter (`artifact: ASTRA_REVIEW_KALAYANTRA_CHARTER`, `version: "1.0"`, `verdict: LAUNCH | LAUNCH_WITH_FIXES | REWORK`, `blocking_count`), then:
1. **Verdict and the five things that matter most** (≤ 400 words).
2. **Findings table** — `ID · severity (BLOCKING/HIGH/MEDIUM/LOW) · file:line · what · why it fails · the fix` — every finding you make, ordered by severity.
3. **Answers A1–G2**, each with file:line evidence.
4. **Corrected artefacts**: for every BLOCKING or HIGH finding in a script or prompt, give the exact replacement text (a diff or the full corrected block), ready to apply.
5. **What to cut** and **what is missing**.
6. **Hashes**: `shasum -a 256` of every file under review.
