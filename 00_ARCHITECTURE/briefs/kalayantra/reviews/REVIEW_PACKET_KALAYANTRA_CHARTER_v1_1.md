# Focused re-review — KĀLA-YANTRA execution design v1.1 (after your REWORK of v1.0)

You are Astra, the independent reviewer. You reviewed v1.0 of this execution design at commit dee68bae and returned REWORK with 27 findings, 11 blocking (`reviews/ASTRA_REVIEW_KALAYANTRA_CHARTER_v1_0.md`). The design has been reworked. This is a **bounded re-review**: decide whether the fleet may now be launched. Read-only: run no builds, open no database connection, write no file except your review.

## What to read (all under /Users/Dev/kalayantra/wt/campaign, branch campaign/kalayantra, head faee6cc91)

- `00_ARCHITECTURE/briefs/kalayantra/reviews/KALAYANTRA_CHARTER_RECONCILIATION_v1_0.md` — the author's disposition of each of your findings, plus nine defects the author found. Treat it as a claim to test, not as evidence.
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md` (v1.1)
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md` (v1.1)
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_KICKOFF_PROMPT_v1_0.md` (v1.1)
- `00_ARCHITECTURE/briefs/kalayantra/prompts/{SUTRADHARA,ADHIKARIN,PARIKSAKA,KARAKA}.md`
- `00_ARCHITECTURE/briefs/kalayantra/fleet/` — `kalayantra_fleet.sh`, `executor.py`, `executor.sh`, `executor_ops.json`, `readback_sql.sh`, `finalize.sh`, `install_tracker.sh`, `preflight.sh`, `precheck.sh`, `local_db.sh`, `verify_specs.sh`, `README.md`
- `00_ARCHITECTURE/control/kalayantra/plan_model.json` — 135 items, generated; each item has `brief`, `depends_on`, `mandatory`, optional `requires_outcome`, a detector; top-level `control_plane`, `coordination`, `coverage`.
- `platform/scripts/governance/pravaha_tracker/` — the tracker package as copied (unchanged; the B-1b capabilities are NOT implemented yet — that is the fleet's first work, by design).
- For the specification side, only as needed: `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md` §4, §7, §8, §9 and `KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md` §3, §5.

## What to decide

**Part 1 — your eleven blockers (KY-01 … KY-11).** For each: `CLOSED`, `PARTLY` or `OPEN`, with file and line evidence. `CLOSED` means the design, as written in these files, no longer has the defect — not that the author says so. Where a remedy is deferred to a fleet item (for example the control-plane capabilities in B-1b), judge whether the launch is **safe before that item lands**: does anything run that depends on the missing capability?

**Part 2 — the launch path, executed in your head.** Walk the kickoff prompt step by step, then the first conductor, surrogate and verifier cycles against the tracker package **as it exists today** (old `start/step/review/done`, no `claim`, no `verdict`, no `audit`). Name the first command that fails or does the wrong thing, if any. In particular check: `kalayantra_fleet.sh up` (snapshot, double fork, lane locks, `wanted` with the two pool files, `reserve_cycle`, the `env -i` list, the Python controller); whether `v2` and the six workers really stay idle; whether `ky preflight` fails for a detached lane before B-1b and what a lane does then; `install_tracker.sh` (snapshot; the `ky` and `kybrief` wrappers; the receipt); `preflight.sh bootstrap` and `launch`; `executor.py` (origin/main table, requesters, private worktree at a merged commit, threads, INTERRUPTED, redaction) and `readback_sql.sh`; `finalize.sh` with lane `v1` left running.

**Part 3 — the plan model.** (a) Is any charter-promised result still outside `JOIN-ALL`'s closure or unowned? Use the `coverage` block and plan §8/§9. (b) Is any dependency wrong in a way that would start work too early, deadlock, or leave an item unreachable? Check especially: B-1 ↔ B-6 ↔ B-3 ↔ B-7; the `requires_outcome` items and their `mandatory` flags (what happens to `JOIN-ALL` and to the definition of done when D-FLIP, D-VC, D-TEARDOWN, D-COMPACT, D-G2, D-T2, D-R6, D-KR end approved, refused, or stay open); K3-2 / V-K3b / K8-K3; K9-4a's gate on the flip. (c) Are the detectors sound — would any read true too early, or never? Check the `file_contains` patterns on `executor_ops.json`, the two `db_query` SQL strings, the `branch_file_contains` ones, and the packet-exit verdict files. (d) Is any item still too large for one 90-minute cycle without a "S splits" note?

**Part 4 — anything new that blocks a launch**, in the changed artefacts only. Do not re-open findings you already raised unless the remedy is wrong.

## How to answer

Start the file with frontmatter: `artifact: ASTRA_REVIEW_KALAYANTRA_CHARTER`, `version: "1.1"`, `verdict: LAUNCH | LAUNCH-WITH-FIXES | REWORK`, `blocking_count: <n>`, `reviewed_commit: faee6cc91`, `review_date`, `review_mode: read-only`.

Then, in this order and nothing else:
1. **Verdict** in five lines.
2. **Part 1 table** — KY-01 … KY-11: status, evidence, what remains.
3. **Findings** — at most **fifteen**, most severe first, numbered `KZ-01…`, each with: severity (`BLOCKING` = the fleet must not be launched until fixed; `HIGH` = fix in the first day, the fleet may launch; `MEDIUM`; `LOW`), file and line, the defect in two sentences, the failure it causes, and the **exact replacement text or code** (a patch the author can apply without interpretation).
4. **What you could not verify** from a read-only position.

Be concrete and sparing. A finding without a line reference and a replacement is not a finding. `LAUNCH-WITH-FIXES` means: no BLOCKING finding remains once the listed patches are applied, and you list which patches those are.
