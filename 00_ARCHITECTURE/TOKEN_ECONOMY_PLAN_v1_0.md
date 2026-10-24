---
artifact: TOKEN_ECONOMY_PLAN_v1_0.md
status: DRAFT — AWAITING NATIVE APPROVAL (Phase B gate)
version: 1.0
authored_by: Claude Code (Opus 5.5), token-economy audit session, worktree audit/token-economy
authored_on: 2026-10-11
audience: native (approver); Phase-B executor; KĀLA-YANTRA / Suvarṇa conductors for the items they own
disposition: >
  Plan of record for reducing token consumption without lowering quality,
  accuracy or signal honesty. Nothing here runs until the native approves item IDs
  or waves. Evidence: 00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md (cited as A§n / F-n / B-n).
---

# Token Economy Plan

## How to read an item

- **Δ (expected impact):** a measured basis, or "estimate" with its basis, or
  "unquantified". It always says which token class moves.
- **Identity:** whether proof is needed that the product's output stays the same
  (rule 7), and how it would be done.
- **Auth:** who must authorise it — the native, another campaign, a deploy window,
  or frozen-code permission.
- **Verify:** re-run `scripts/token_economy/token_baseline.py` over the same window
  length, before and after, unless stated otherwise.
- **Merges:** never by the executor. Every PR is reviewed independently in a separate
  session.

**Ownership boundary.** KĀLA-YANTRA's fleet scripts live outside the repo, in
`/Users/Dev/kalayantra/{fleet_live,conductor,bin}`, plus
`~/.config/kalayantra/fleet.env`; its briefs live in-repo under
`00_ARCHITECTURE/briefs/kalayantra/`. Every item touching them is marked
**Auth: KĀLA-YANTRA conductor + native**. The executor prepares the change as a patch
or PR and does not apply it to a running fleet.

---

## Wave 0 — Quick wins in configuration and always-loaded context (no product risk)

### W0-1 Commit the corrected baseline meter
- **Finding:** A§3 (the meter is NOT trustworthy) and F-10.
- **Change:**
  - Add `scripts/token_economy/token_baseline.py` (the Phase-A script) plus a golden
    test: a synthetic transcript with duplicate content-block lines, a partial first
    line, a cross-file resumed key, a workflow-agent file, a Codex rollout and a fleet
    log, each with known four-class totals.
  - Add a `--check` mode that fails if any related-looking folder is unmatched.
  - Discover folders from `git worktree list --porcelain` as well as the token match.
- **Δ:** none directly. It is the instrument every other item is verified with.
- **Risk:** none.
- **Identity:** not needed.
- **Effort:** S. **Deps:** none. **Auth:** native (new file in the repo).
- **Verify:** the golden test passes, and the totals reproduce A§2 B-1 within 0.1 %
  on the same window.
- **Rollback:** delete the file.

### W0-2 Declare the Nirmāṇa spend meter and its ceilings null
- **Finding:** A§3. The in-run ceiling is enforced only by an LLM prompt (§N.8).
- **Change:** a short note in `00_ARCHITECTURE/autonomy/` on main recording that
  `spend_meter.py` (branch `campaign/nirmana-autonomous`) is untrustworthy. The note
  gives the defect list, and says ceiling statuses are null until a code-computed
  replacement exists. No edit to the dormant branch.
- **Δ:** none. This is signal honesty.
- **Risk:** none. **Identity:** no. **Effort:** XS. **Auth:** native.
- **Verify:** n/a. **Rollback:** revert the note.

### W0-3 Load MARSYS once
- **Finding:** F-2. The deny entry `"claude.ai Marsys JIS"` does not match the actual
  name `"claude.ai MARSYS-JIS"`, so 131 tool names load twice.
- **Change:** correct the deny name in the setting the native chooses, or disconnect
  `marsys-jis-direct` for Madhav sessions. Recommended: keep `marsys-jis-direct` (its
  names are shorter: 1,983 vs 2,376 tik).
- **Δ (estimate):** −2.0 to −2.4 k cache_read per Claude call. Over 152,711 calls in
  30 days that is ≈ 0.3–0.37 B cache_read per 30 days, if subagents also carry the
  names (to be confirmed by re-measuring a subagent's first call).
- **Risk:** low. A session that needs the other copy loses it. The tools are
  identical (131 each).
- **Identity:** no (developer tooling).
- **Effort:** XS. **Auth:** native decides which copy stays.
- **Verify:** first-call context of a new interactive session and a new subagent,
  before and after.
- **Rollback:** restore the setting.

### W0-4 Remove unrelated plugins and connectors from Madhav sessions
- **Finding:** F-2. Skills from claude.ai plugins (small-business, zoominfo, marketing,
  data, enterprise-search, zapier) and the Shopify, Playwright, Wispr, Drive and
  Calendar MCPs: EST 6–10 k tokens per turn.
- **Change:** a project-scoped `enabledPlugins`/MCP disable in
  `.claude/settings.json` (repo) or `settings.local.json`, so other projects are
  unaffected. The executor confirms the exact keys against current Claude Code docs
  before editing.
- **Δ (estimate):** −6 to −10 k cache_read per call on calls that carry it, ≈ 0.9–1.5 B
  per 30 days if it applies to all 152,711 calls. A first-call re-measure decides
  which calls it reaches.
- **Risk:** low. Anything the native genuinely uses in Madhav stays on an allow-list.
- **Identity:** no. **Effort:** S. **Auth:** native (list review).
- **Verify:** first-call context before and after.
- **Rollback:** revert the settings file.

### W0-5 Pin deferred MCP tool loading
- **Finding:** F-2. Deferral is on by default but not pinned. If it were off, MARSYS
  definitions alone would add 138–210 k tokens per turn.
- **Change:** set the tool-search/deferral setting explicitly in project settings,
  after verifying its exact name in the docs.
- **Δ:** 0 today. Protects against a ≈ +140–210 k per-turn regression.
- **Risk:** none. **Identity:** no. **Effort:** XS. **Auth:** native.
- **Verify:** the MCP tools still show as deferred in a fresh session.
- **Rollback:** remove the key.

### W0-6 Turn off Codex memories for fleet lanes
- **Finding:** F-4. The ~8.7 k "Memory" block is re-sent every turn, and `MEMORY.md`
  (270 KB) is searched in 3,584 of 4,079 cycles.
- **Change:** one line, `memories = false`, in the profile written by
  `/Users/Dev/kalayantra/fleet_live/make_codex_profile.sh`.
- **Δ (estimate):** 8.7 k × 9–19 turns × ~1,100 cycles a day ≈ 86–182 M gross per day,
  mostly cached input, plus the uncached tokens of the `MEMORY.md` searches. Basis:
  the 10-09 cycle count.
- **Risk:** low. Lanes lose cross-session recall of Codex memories; their durable
  state is in the tracker and `run/`, not memories.
- **Identity:** no. **Effort:** XS.
- **Auth:** KĀLA-YANTRA conductor + native.
- **Verify:** footer and gross tokens per cycle, by role, over 2 days before and after.
- **Rollback:** remove the line.

### W0-7 Root AGENTS.md must not send Codex lanes to read CLAUDE.md in full
- **Finding:** F-4. 2,513 cycles read `CLAUDE.md`; the cycle preamble says it does not
  govern the fleet.
- **Change:** reword root `AGENTS.md` to "read CLAUDE.md sections relevant to the
  task; fleet lanes follow their role card".
- **Δ (estimate):** ≈ 1–3 M footer tokens per day, plus the gross multiplier on later
  turns.
- **Risk:** low. Interactive Codex sessions could skip a rule they needed. Mitigated
  because CLAUDE.md is now 3.6 k and is still named.
- **Identity:** no. **Effort:** XS. **Auth:** native (governance file).
- **Verify:** count of fleet cycles that `cat` CLAUDE.md, before and after.
- **Rollback:** revert.

### W0-8 Keep 90 days of Claude transcripts
- **Finding:** A§2. Transcripts are pruned after 30 days, so no longer baseline is
  possible.
- **Change:** set `cleanupPeriodDays: 90` in user settings.
- **Δ:** none. Costs ≈ 2.8 GB more disk at today's rate (3.9 GB holds ≈ 30 days of all
  projects).
- **Risk:** disk only. **Identity:** no. **Effort:** XS. **Auth:** native.
- **Verify:** 31-day-old transcripts still present after 31 days.
- **Rollback:** revert the setting.

### W0-9 Run the paid Paripraśna smoke only after production (main) deploys
- **Finding:** F-8. Up to ~90 paid production turns a day, including PR-triggered
  deploys.
- **Change:** restrict the trigger of `.github/workflows/pariprashna-post-deploy-smoke.yml`
  to main deploys, or add a daily cap.
- **Δ:** product API spend (Gemini synthesis). The four-class figures are NOT MEASURED
  (they need the metering ledger). Fewer runs is certain.
- **Risk:** **signal coverage.** PR deploys lose their live end-to-end check. The
  14-of-42 failure rate suggests the check matters, so this is an owner decision.
- **Identity:** no (CI only). **Effort:** XS. **Auth:** native.
- **Verify:** workflow run count per day.
- **Rollback:** revert the workflow.

---

## Wave 1 — Workflow changes and the fleet re-roster

### W1-1 Start a fleet cycle only when there is work (the biggest fleet lever)
- **Finding:** F-3. Over 10-06 → 10-10, 1.25 B gross went to no-work cycles and 766 M
  to claim-renew polling, out of 3.13 B gross; on 10-09, 61 % of 801 M.
- **Change:** a deterministic pre-cycle probe in `kalayantra_fleet.sh` (no model) that
  launches a cycle only if one of these holds:
  - a new PR head without a verdict;
  - a new inbox message;
  - a READY item the lane may claim;
  - a failed check on the lane's own PR;
  - a claim nearing renewal (renewal itself becomes a script action).

  Otherwise the lane sleeps on a backoff (60 s → 600 s → 1,800 s). A cycle that only
  renewed a claim counts as idle. All lanes honour `HOLD_MERGES`.
- **Δ (measured basis):** up to ≈ 64 % of fleet gross was addressable in the window
  (2.02 B of 3.13 B). Expected 50–60 % of fleet tokens, ≈ 0.4–0.5 B gross per day at
  the 10-09 rate. All four classes fall roughly in proportion.
- **Risk:**
  - A slower reaction to new work, bounded by the probe interval.
  - A probe bug could starve a lane. Mitigation: the probe logs every decision, and
    one forced cycle per lane every 2 h acts as a liveness floor.
- **Identity:** no (fleet, not product).
- **Effort:** M. **Deps:** W0-1 for measurement.
- **Auth:** KĀLA-YANTRA conductor + native. It changes fleet scheduling, not the
  FROZEN orchestrator.
- **Verify:** cycles per day, idle share and gross per accepted item, over 3 days
  before and after. The accepted-items rate must not drop.
- **Rollback:** env flag `KY_WORK_PROBE=0`.

### W1-2 Role cards instead of whole-document reads
- **Finding:** F-4. The charter (18.6 k tik) was read in 3,106 cycles and the
  amendment in 2,623; ≈ 12 M footer tokens a day plus the gross multiplier.
- **Change:**
  - One card per role, each ≤ 1.5 k tokens: the binding rules from the charter v1.1
    and the velocity amendment v2.0, with section anchors.
  - The role prompt says "read the card; open charter §X only when the card points
    there".
  - Paired-prompt rule: the cards are regenerated whenever the charter or amendment
    changes, and a CI check compares card version stamps with source versions.
- **Δ (estimate):** −10 to −12 M footer per day; gross larger.
- **Risk:** **rule loss.** A card that omits a binding rule lowers quality. Mitigation:
  the ADHIKĀRIN or native signs off each card, and a rule-coverage checklist maps
  every MUST in the source to a card line.
- **Identity:** no. **Effort:** M.
- **Auth:** KĀLA-YANTRA conductor + native (charter-derived governance).
- **Verify:** charter and amendment read counts per cycle, and footer per cycle, by role.
- **Rollback:** revert the prompts.

### W1-3 Self-contained work packets
- **Finding:** F-5. Briefs are pointers; builders run 14 commands (p90 43) before
  their first edit; 77 % of rework was preventable.
- **Change:** `kybrief` emits:
  - target files and globs;
  - the signatures to create or change;
  - the PLAN/ALGO excerpts inline (quoted, with an anchor);
  - the text of any rulings;
  - an **executable** acceptance command (the test path plus a precheck item);
  - the migration class.

  The brief author (Opus xhigh) writes the acceptance tests first (shared with W2-4).
- **Δ (estimate):** fewer exploration calls and fewer rework rounds. Unquantified
  until a before/after on ~20 items. Moves input, cache_read and output.
- **Risk:** more upfront planner tokens, which is intended. A wrong inline excerpt
  misleads more than a pointer does, so every excerpt carries its source anchor and a
  hash.
- **Identity:** no. **Effort:** M–L. **Deps:** W1-2.
- **Auth:** KĀLA-YANTRA conductor + native.
- **Verify:** median commands before first edit, verdict rounds per accepted item, and
  gross per accepted item.
- **Rollback:** the old `kybrief` stays available behind a flag.

### W1-4 Verifiers review the diff, with deterministic gates first
- **Finding:** F-5. Verifiers ran `cat` 733 times against `git diff` 38.
- **Change:**
  - The verifier packet = the diff, the brief, and the precheck/test output (already
    deterministic: `precheck.sh`, `verify_specs.sh`, `readback_sql.sh`).
  - The verifier prompt requires reading the diff first. Opening a file beyond the
    diff needs a stated reason.
  - The deterministic gates must be green before a verifier cycle starts.
- **Δ (estimate):** verifier gross per verdict down; unquantified.
- **Risk:** **a narrower review could miss cross-file effects.** The prompt keeps "open
  callers or callees of changed symbols"; the risk-scaled review stays. The verifier
  stays frontier.
- **Identity:** no. **Effort:** S–M.
- **Auth:** KĀLA-YANTRA conductor + native.
- **Verify:** verdict quality (the reversal rate in `EVENTS.jsonl`) must not rise;
  gross per verdict.
- **Rollback:** revert the prompt.

### W1-5 Session-lifetime discipline for interactive coordinators (the biggest overall lever)
- **Finding:** F-1. The top 3 coordinator sessions used 33.9 B in 30 days.
  Main-thread context averages ≈ 557 K tokens per call; sessions run 10–16 days.
- **Change (working practice; owner decision):**
  - **Hand-off.** When a coordinator's context passes a threshold (proposed: 250 K),
    it writes a hand-off note (state, open PRs, decisions, next steps; ≤ 5 k) into its
    campaign folder and the native starts a fresh session from it.
  - **Smaller subagent tasks.** One PR-sized unit per subagent. Read-only sweeps use
    `Explore` (≈ 30 k start vs 62 k).
  - **Short command output.** Subagents keep command output short (`| tail -n 50`,
    quiet test reporters; logs go to files, not context).
  - **Campaign briefs** state the threshold.
- **Δ (estimate):** main-thread context tokens scale roughly with the average context
  per call. Halving that average (557 K → ~280 K) would save ≈ 13 B cache_read per 30
  days on the 27.2 B main-thread base. Subagent tightening saves more on the 26.6 B
  subagent base. *This is a scenario, not a measurement.*
- **Risk:** **continuity.** A fresh session can lose tacit context. Mitigation: a
  structured hand-off template with a checklist, and campaign state stays in files
  and PRs as it already must (§K).
- **Identity:** no. **Effort:** S (documents and templates).
- **Auth:** native (changes how campaigns run).
- **Verify:** context p50/p90 per call, and tokens per merged PR per campaign, over 7
  days before and after.
- **Rollback:** stop applying the threshold.

### W1-6 Lean launch profile for long autonomous interactive work
- **Finding:** F-2. A headless first call is 20–22 k; an interactive one is 47–77 k.
- **Change:**
  - A documented launcher (`scripts/token_economy/claude-lean.sh`):
    `--strict-mcp-config --mcp-config <marsys-only.json>` plus a narrow
    `--setting-sources`. MARSYS is attached only when the task needs chart data.
  - Repo subagent definitions get explicit `tools:` lists. Reviewers don't need
    Write or Edit.
  - No forced `model:` changes (see W1-7).
- **Δ (estimate):** −25 to −55 k cache_read per call for sessions launched this way.
- **Risk:** a missing tool interrupts a session; it can be added back per task.
- **Identity:** no. **Effort:** S. **Auth:** native.
- **Verify:** first-call context; tool-denied events.
- **Rollback:** use the normal launch.

### W1-7 Fleet re-roster to the owner's targets, and pool balancing
- **Finding:** A§5 roster.
- **Change** (fleet.env per-lane `KY_AGENT_*` / model):
  - Conductor and ADHIKĀRIN → Claude Opus 5.5 high (owner target).
  - Verifiers stay frontier. **Recommendation: Codex carries them** (gpt-6.1-sol
    high; diff-only per W1-4), keeping Claude Max for conductor, ADHIKĀRIN, planner
    and interactive coordinators.
  - Builders: an interim Codex gpt-5.6-terra at medium (it edited more per cycle at
    similar tokens) until W2 lands.
  - PRAHARĪ stays a script (it already meets the target).
  - LEKHAKA: not added unless the digest burden on the conductor is shown to matter.
    If added, Haiku 5.5 or a local small model.
- **Δ:** this shifts load between pools rather than reducing it. Moving the conductor
  and ADHIKĀRIN from Codex to Claude adds ≈ 0.07 B gross per day to Claude at 10-09
  rates (after W1-1, smaller).
- **Risk:**
  - **The Claude pool already carries 81 % of tokens, and its quota headroom is NOT
    MEASURED.** Watch for Claude rate limits after the move.
  - Codex weekly use is 33 %.
- **Identity:** no. **Effort:** S. **Deps:** W1-1 first, so idle cycles don't move
  pools.
- **Auth:** native + KĀLA-YANTRA conductor.
- **Verify:** per-pool four-class totals; Codex `used_percent`; any Claude limit events.
- **Rollback:** revert fleet.env.

### W1-8 Fewer conflicts: regenerate generated files instead of merging them
- **Finding:** F-6. 88 conflict cycles at ≈ 2.2 M gross each; generated census files
  are a recurring cause.
- **Change:**
  - A deterministic `regen-generated.sh` step that the supervisor runs when a lane's
    PR conflicts only in generated files (census, writer digests).
  - Lanes refresh from main before claiming, not mid-item.
- **Δ (measured basis):** up to ≈ 197 M gross per 5 days addressable.
- **Risk:** a regeneration with the wrong tool version. The script pins the
  generator and fails closed.
- **Identity:** no (generated artifacts are checked by existing CI). **Effort:** M.
- **Auth:** KĀLA-YANTRA conductor; Suvarṇa owns the census generator.
- **Verify:** conflict cycles per day.
- **Rollback:** disable the step.

---

## Wave 2 — Local-builder enablement (gated on owner decision OD-1)

### W2-0 Hardware reality check (decision, not code)
- **Finding:** A§7. The machine is an M5 Pro with 64 GB, not an M5 Max with 128 GB.
  The model name "Qwen3.8-27B" is unverified.
- **Options:**
  - (a) One builder at 8-bit.
  - (b) Two builders at 4–6-bit.
  - (c) Run the local builder on other hardware.

  Recommendation: **(a)** first, measured, then decide.
- **Auth:** native.

### W2-1 Install and verify the local harness
- **Change:** pull the chosen model into the running Ollama. Verify two routes on one
  fixture packet:
  1. `codex exec --oss --local-provider ollama` (the smallest change to the fleet);
  2. Claude Code with `ANTHROPIC_BASE_URL=http://127.0.0.1:11434`.

  Record tokens per second, time to first token, context limit and memory peak.
- **Δ:** none yet.
- **Risk:** memory pressure on the native's working machine (Docker, Postgres, IDEs).
- **Identity:** no. **Effort:** S. **Deps:** W2-0.
- **Auth:** native (installs a model of ~30 GB).
- **Verify:** the fixture packet goes green locally.
- **Rollback:** `ollama rm`.

### W2-2 A `local` agent type and lanes in the supervisor
- **Change:**
  - `kalayantra_fleet.sh` gets `KY_AGENT_<lane>=local` and lanes `l1`/`l2`, sized by
    `run/KY_LOCAL_WORKERS` (0–2).
  - Add the endpoint variable to the `lane_env` allow-list.
  - Run one Ollama process with `OLLAMA_NUM_PARALLEL` equal to the number of local
    lanes and a single loaded model.
  - Local lanes claim only `build_tier=local` items.
- **Worktrees:** under `/Users/Dev/worktrees.noindex/madhav/<harness>/kalayantra-<id>/`
  per the owner's folder policy. `<harness>` is the driving CLI (claude or codex),
  because the policy names tools, not models. The claude root currently holds 11 of
  its 15 allowed copies.
- **Risk:** scheduling bugs; the existing heavy-step precheck lock stays.
- **Effort:** M. **Deps:** W2-1, W1-1.
- **Auth:** KĀLA-YANTRA conductor + native.
- **Verify:** a local lane completes 3 fixture items.
- **Rollback:** `KY_LOCAL_WORKERS=0`.

### W2-3 Build-tier router with frontier-by-rule classes
- **Change:** packet fields `build_tier`, `acceptance_tests` and `max_local_loops`
  (default 3). A router computes the tier from the globs below and re-runs on the
  **actual diff**; any frontier hit discards the local work. The tier can only be
  raised by hand, never lowered.
- **Frontier by rule:**
  - Gaṇita computation core: `python-sidecar/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**`,
    `orchestrator/writers/ga_*.py`, `services/{kala_core/sky,gochara_kernel}/**`,
    `**/*ephemeris*`, `platform/scripts/temporal/**`, and any importer of swisseph or jhora.
  - All migrations: `platform/migrations/*.sql`, `platform/supabase/migrations/*.sql`,
    `scripts/migrate.ts`, any `GRANT`, and protected-window items.
  - FROZEN orchestrator files: `pipeline/orchestrator/{writers/__init__.py,asset_runner,runner,staleness,global_runner,verification_job,seal_job,locks,db,provenance*,output_digest,writer_runtime_support,dag_edge_guard}.py`.
  - Any diff line touching `'lit'` state or writing `verification_pass_status`, plus
    `brahmagyan/verification_{vocab,tiers}.py`, `ga_writers/gates.py`,
    `*_independent_verifier.py`, `*/_idempotency.py`.
  - Security and auth: `src/proxy.ts`, `src/lib/{auth,security,share,limits,mcp}/**`,
    `src/app/api/{auth,admin,db}/**`, `src/app/share/**`, `scripts/*preflight*.ts`,
    `scripts/data-plane-*.ts`, `.github/workflows/**`, `infra/**`, Dockerfiles.
  - Governance detectors and the control plane: `platform/scripts/governance/**`,
    `00_ARCHITECTURE/briefs/kalayantra/fleet/**`, `pravaha_tracker/**`.
- **Risk:** mis-routing; mitigated by the second router pass on the diff.
- **Effort:** M. **Auth:** native (these lists are policy).
- **Verify:** the router agrees with hand classification on the last 150 PRs (A§7).
- **Rollback:** route everything to frontier.

### W2-4 Acceptance tests are written first, by frontier
- **Change:** before a local build, the brief author writes or approves executable
  tests. They must fail on the base commit and pass on the branch, and `precheck.sh
  --item` must be green.
- **Escalation to frontier:** after 3 red loops, or 1 verifier rejection, or a
  frontier-rule hit, or more than 90 minutes, or 2 server or context errors. The
  frontier builder inherits the branch and the logs.
- **Risk:** weak local models writing self-passing tests is exactly what this removes.
- **Effort:** M. **Deps:** W1-3. **Auth:** native.

### W2-5 Local-run metering
- **Change:** one row per run in `run/LOCAL_RUNS.jsonl`: item, loop, model,
  quantisation, context, prompt and completion tokens (Ollama reports them), time to
  first token, tokens per second, wall time, precheck and test results, escalated
  (and why), verdict.
- **Reporting:** the baseline script gets a `--local` reader. Local runs show as a
  separate pool, never mixed into subscription totals.
- **Effort:** S. **Auth:** KĀLA-YANTRA conductor.

### W2-6 A code map and conventions card for builders
- **Finding:** A§7 risks 2–4.
- **Change:**
  - `00_ARCHITECTURE/CODE_MAP_v1_0.md`: generated by a deterministic script from the
    tree, entry points and module docstrings, and regenerated by CI. Frontier and
    local builders both benefit.
  - A ≤ 2 k conventions card covering §N.2–N.7 essentials, `verification_vocab`
    constants, `_idempotency.py`, writer digests, migration numbering, and the
    Next.js 16 `src/proxy.ts` / React 19 / Zod 4 differences.
- **Δ (estimate):** fewer exploration calls for every builder; unquantified.
- **Risk:** a stale map; mitigated by CI regeneration and a hash check.
- **Effort:** M. **Auth:** native (new canonical artifact; register it in
  `CAPABILITY_MANIFEST.json`).

### W2-7 Offline test parity
- **Change:** pin the local test Postgres to 15.18, matching CI. Document the offline
  test command per packet type.
- **Risk:** none. **Effort:** S. **Auth:** native.

---

## Wave 3 — Product-runtime optimisations (every item gated on proof the output is unchanged)

**Common identity method:**
- A frozen corpus of ≥ 50 recorded consult and Paripraśna requests (chart, question,
  flags).
- Run old and new with the same model, seed and temperature where supported.
- Compare the planner's selected capabilities (set-equal), the bundle hash, the
  assembled prompt (byte-equal where claimed), citations, and the final answer under
  a semantic-equivalence judge plus golden-value checks (§N.7.5).
- "Byte-identical" claims need an actual byte comparison (§N.8 instance 3).

### W3-0 Honest runtime telemetry (prerequisite; no output change)
- **Finding:** A§6. Planner, title and tool-loop telemetry write constant 0 for cache
  and reasoning; MCP `token_estimate: 0`; no response sizes; inconsistent pricing rows.
- **Change:**
  - Record the provider-reported cache_read, cache_write and reasoning tokens for the
    planner, title and tool loop.
  - Log MCP response bytes and the class of tokens used.
  - Reconcile the opus-4-7 price rows (`seed_v1.ts:122`, migration 583,
    `registry.ts:1222`). Any migration is a new migration, never an edit to an applied one.
- **Δ:** none (measurement).
- **Risk:** none to output.
- **Identity:** prove that request bodies are byte-identical before and after (only
  logging changes).
- **Effort:** M.
- **Auth:** native and a deploy window. It touches the metering path only, not
  frozen code.

### W3-1 Prompt caching on the Anthropic synthesis path
- **Finding:** A§6. `chat()` ignores the cache config (`anthropic/adapter.ts:93-128`).
- **Change:** honour cache breakpoints after the fixed system and CGM blocks.
  **Phase 1:** no reordering, so the prompt stays byte-identical and only billing
  changes. **Phase 2 (output-changing):** move the dated temporal anchor after the
  fixed blocks to raise the cache-hit rate.
- **Δ:** cache_read replaces input on repeated prefixes. Unquantified until W3-0;
  depends on how much traffic uses the Anthropic stack (the default is Gemini).
- **Risk:** Phase 1 none; Phase 2 medium.
- **Identity:** Phase 1 byte-equal prompt; Phase 2 the full corpus method.
- **Effort:** S / M. **Auth:** native; Phase 2 is an owner decision.

### W3-2 Gemini explicit cache for the planner system prompt (26.8 k)
- **Finding:** A§6. The explicit cache is hard-disabled (`if (false && …)`, `:514`).
- **Change:** first find out why it was disabled (git blame and the PR discussion).
  Re-enable it only for the static planner system prompt.
- **Δ:** a per-call input discount on 26.8 k tokens for every consult turn;
  unquantified until W3-0.
- **Risk:** stale cache when the prompt changes; key the cache on the prompt hash.
- **Identity:** byte-equal prompt, with the plan-equivalence part of the corpus method.
- **Effort:** S–M. **Auth:** native + deploy window.

### W3-3 Stop sending MCP output twice
- **Finding:** A§6. Responses of 50,000 bytes or less go out as structured content and
  as text (`registry_bridge.ts:1931-1966`).
- **Change:** send text only when the client lacks structured-content support, or
  send a one-line text summary.
- **Δ:** up to ≈ half the response tokens for clients that read both copies (client
  behaviour NOT MEASURED).
- **Risk:** low–medium. Some clients rely on the text copy.
- **Identity:** the JSON payload is byte-equal; the text channel changes. **Output-
  changing for clients → owner decision.**
- **Effort:** S. **Auth:** native + deploy window.

### W3-4 Binding MCP byte ceiling, plus `fields`/`cursor` on the largest tools
- **Finding:** A§6. The budget is soft, and `assess_*`, `ganita_chart_facts_get` and
  `ganita_structural_get` responses reached 117–307 KB (July, pre-cap).
- **Change:**
  - First re-measure on current main.
  - Then add `fields` and `cursor` to the 5 largest tools.
  - Make the ceiling binding by paginating, never by dropping rows (B.10, §N.6
    density rules: protect hard-floor sections first).
- **Risk:** medium. A §N.6 violation if trimming hides confirmed findings.
- **Identity:** set-equality of rows across pages against the unpaginated response.
  Output-changing → owner decision.
- **Effort:** M. **Auth:** native + deploy window.

### W3-5 Smaller planner input
- **Finding:** A§6. A ≈ 57–66 k planner input; multi-school examples repeat the
  capability payload (≈ 3×); the repair call re-sends everything.
- **Change:** the examples reference the payload once; per-capability fields are
  trimmed; the repair call sends only the failing fields.
- **Δ (estimate):** −20 to −40 k input on multi-school turns.
- **Risk:** **high.** Plan selection may change.
- **Identity:** plan-equivalence across the corpus (selected capability sets equal on
  ≥ 98 % of requests; every difference reviewed). **Owner decision.**
- **Effort:** M.

### W3-6 Cap the bundle and tool-loop results; resolve F1-runtime
- **Finding:** A§6. No byte cap on the bundle; uncapped tool results across up to 8
  rounds; synthesis may not receive the planner's results.
- **Change:** confirm F1 with one traced request body **first**. That is a correctness
  question for the native. Then propose caps.
- **Risk:** **high**; the content the model sees changes.
- **Identity:** full corpus method. **Owner decision.**
- **Effort:** M–L.

### W3-7 History replay
- **Finding:** A§6 F2-runtime. Compression replays up to ~32 k and overrides the
  planner's 2-turn window.
- **Change:** an owner decision on the intended behaviour, then align the code and flag.
- **Risk:** medium (multi-turn coherence).
- **Identity:** the corpus method on multi-turn conversations. **Owner decision.**

### W3-8 Explicit thinking level for the fast planner
- **Finding:** A§6. It inherits `'high'`.
- **Change:** set it explicitly; test `medium` against `high`.
- **Risk:** medium (plan quality).
- **Identity:** plan-equivalence. **Owner decision.**

---

## Phase-B ordering and gates

1. **Wave 0 first,** one PR. W0-6 is sent to KĀLA-YANTRA as a patch. User-level
   settings (W0-3, W0-4, W0-8) are applied only on the native's word.
2. **W1-1 before W1-7.**
3. **W2 only after OD-1.**
4. **W3-0 before any other W3 item.**
5. **Before every PR:**
   - the deterministic gates (`/run-checks`; governance validators where touched);
   - for W3, the identity proof;
   - a baseline re-run with the delta shown, or "measurable only after N days of use"
     where that is honest;
   - an independent review in a separate session.

## Owner decisions needed

- **OD-1 — Local builder hardware.** The machine is an M5 Pro with 64 GB, not an M5
  Max with 128 GB. Choose 1 builder at 8-bit, 2 at 4–6-bit, or other hardware.
  Confirm the model ("Qwen3.8-27B" is unverified).
- **OD-2 — Coordinator session lifetime (W1-5).** Adopt a context threshold with
  hand-off notes for campaign coordinators? Proposed: 250 K.
- **OD-3 — Which MARSYS connection stays in Claude Code (W0-3).** Recommend
  `marsys-jis-direct`.
- **OD-4 — Plugins and connectors** to keep enabled in Madhav sessions (W0-4).
- **OD-5 — Pool balancing (W1-7).** Conductor and ADHIKĀRIN move to Claude Opus (your
  target) while Codex carries the verifiers and interim builders. Risk: Claude quota
  headroom is NOT MEASURED, and Claude already carries 81 % of tokens.
- **OD-6 — Paid deploy smoke scope (W0-9):** main deploys only, versus every deploy.
- **OD-7 — KĀLA-YANTRA changes** (W0-6, W1-1, W1-2, W1-3, W1-4, W1-8, W2-2). Approve
  them, and have the KĀLA-YANTRA conductor apply them. The fleet is outside the repo
  and is running.
- **OD-8 — Runtime items that change output** (W3-1 phase 2, W3-3 to W3-8). Each needs
  your decision after its identity report.
- **OD-9 — F1-runtime correctness question:** does consult synthesis receive the
  planner's tool results? Investigate now, separately from token work?
- **OD-10 — LEKHAKA:** leave absent (recommended), or add one as Haiku 5.5 or local?

## Explicitly not doing, and why

- **Moving any fleet to pay-per-token API billing.** Owner decision: stay on
  subscriptions.
- **A local or cheaper verifier.** Owner decision: PARĪKṢAKA stays frontier.
- **Reducing verification rigour** (fewer verifier passes, skipping precheck) to save
  tokens. It lowers signal honesty. W1-4 narrows what verifiers *read*, not what they
  *check*.
- **Editing the FROZEN orchestrator.** It makes no LLM calls. Its only token
  relevance is through builders touching it, handled by the frontier-by-rule router.
- **Generative-LLM curation in writers.** None exists, and the deterministic-first
  rule stays.
- **Trimming root CLAUDE.md further.** It is already 3.6 k; moving §N.6–N.8 out saves
  ~0.7 k per turn against real rule-loss risk.
- **Reviving or patching the Nirmāṇa fleet or its meter.** It is dormant since
  2026-09-09. W0-2 records that its signals are null, and its useful fixes are carried
  by W0-1. If it is ever revived, remove its "re-read CAMPAIGN_STATE.json (103 k tik)
  every 60 s" step first.
- **Deleting old transcripts or logs to "save" tokens.** Storage is not tokens, and
  they are the audit trail.
- **Forcing cheaper `model:` on repo review subagents.** Reviewer quality matters more
  than the saving. W1-6 scopes their tools only.
- **Any change to production DB flags or deploys during Phase A.** Ground rules.

## Changelog

- v1.0 (2026-10-11): initial plan, pending native approval.
