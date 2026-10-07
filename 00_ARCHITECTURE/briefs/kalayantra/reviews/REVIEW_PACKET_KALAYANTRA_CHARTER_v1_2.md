# Confirmation review — KĀLA-YANTRA execution design, head 8f5bcaf89 (after your second REWORK at faee6cc91)

You are Astra. You reviewed this design twice: v1.0 (27 findings) and v1.1 at faee6cc91 (REWORK; KZ-01 … KZ-13, three blocking). Every KZ finding has been applied, most with your exact replacement, two with a stated amendment. This is a **short confirmation pass**: is a launch now safe? Read-only: run no build, open no database connection, write no file except your review.

## Read (all under /Users/Dev/kalayantra/wt/campaign at head 8f5bcaf89)

1. `00_ARCHITECTURE/briefs/kalayantra/reviews/KALAYANTRA_CHARTER_RECONCILIATION_v1_0.md` §3 items 10–15 and §3b — the author's claims. Test them; do not trust them.
2. `00_ARCHITECTURE/briefs/kalayantra/fleet/`: `executor.py`, `executor_ops.json`, `readback_sql.sh`, `finalize.sh`, `local_db.sh`, `precheck.sh`, `kalayantra_fleet.sh`, `make_codex_profile.sh`, `preflight.sh`, `install_tracker.sh`, `executor.sh`.
3. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_KICKOFF_PROMPT_v1_0.md`, `KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md` §3.2, §4.1, §4.3, §4.4, §7, §12, §15, and `prompts/{SUTRADHARA,ADHIKARIN,PARIKSAKA,KARAKA}.md`.
4. `00_ARCHITECTURE/control/kalayantra/plan_model.json` (143 items; `join`, `accepts_not_applicable_dependencies`, `mandatory`, `requires_outcome`, `control_plane`).

New since your last review, which you have not seen: the lanes run under a **generated Codex profile** (`make_codex_profile.sh`: every personal MCP server and plugin of the operator's base configuration switched off), a **generated shell start-up** (ZDOTDIR) with an explicit tool path, worker model `gpt-6-sol`, a standing **lane smoke** gate (`kalayantra_fleet.sh smoke`), a **dry-run** switch, usage-limit detection narrowed to Codex's own error lines of a failed cycle, item K0a-0 (CI really runs the campaign's database tests), K8-R26, and the hand-off items B-1p / B-1v.

## Decide

**Part 1 — KZ-01 … KZ-13:** for each, `CLOSED`, `PARTLY` or `OPEN`, with file:line evidence at head 8f5bcaf89. For the two amendments (KZ-03: the acceptance is valid three hours, not fifteen minutes, and required rows are declared per kind in the operations table; KZ-10: restore errors are judged against an allow-list of nine expected ones instead of stop-on-error) say whether the amendment is sound or reopens the defect.

**Part 2 — the launch path once more, in your head, at head 8f5bcaf89:** kickoff Steps 0–5, then the first cycles of `sutradhara`, `adhikarin` and `v1` under the pre-B-2 protocol with the unmodified tracker package. Name the first command that fails or does the wrong thing, if any. Include the new code: `lane_env`, `ensure_shell_home`, `make_codex_profile.sh`, `smoke`, `quota_error_in`, the `wanted` gates, and whether a lane can still obtain a credential or a personal tool by a deterministic route.

**Part 3 — anything new that blocks a launch** in the files changed since faee6cc91. Do not re-open a closed finding unless its remedy is wrong.

## Answer format

Frontmatter: `artifact: ASTRA_REVIEW_KALAYANTRA_CHARTER`, `version: "1.2"`, `verdict: LAUNCH | LAUNCH-WITH-FIXES | REWORK`, `blocking_count`, `reviewed_commit: 8f5bcaf89`, `review_date`, `review_mode: read-only`.

Then only: (1) the verdict in at most five lines; (2) the Part 1 table; (3) findings — **at most eight**, numbered `KW-01…`, each with severity (BLOCKING = must be fixed before launch; HIGH = first day; MEDIUM; LOW), file:line, the defect in two sentences, the failure, and the **exact replacement**; (4) what you could not verify. A finding without a line and a replacement is not a finding. `LAUNCH-WITH-FIXES` means no BLOCKING finding remains once the listed patches are applied — list them.
