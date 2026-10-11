# COVERAGE_BOOTSTRAP — B-0c cards (DRAFT — pending the B-0c independent review)

Maps every applicable MUST of root CLAUDE.md §I and §N.1–§N.8, decisions D-1, D-6 (revised), D-9, findings KV-08 and KW-02, and plan §3 "Kept" to the card line(s) that carry it in `BOOTSTRAP.md` (BS), `FIXTURE_BUILDER.md` (FB), `FIXTURE_VERIFIER.md` (FV) and `OWNER_SURROGATE.md` (OS). Sources as tracked at commit `e709f60d7fcd4559227a25a4d5d83d6431c396b6`: `KALAYANTRA_RELAUNCH_PLAN_v2_7.md`, `KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md`, `.claude/agents/kalayantra-owner-surrogate.md`; root `CLAUDE.md` v8.0.

Cell values: line ids = carried by those card lines · **N/A** = not applicable to this role, with the reason · **packet** = not a card line; must be a packet clause whenever a packet touches it (plan §3 allows a card line, a packet clause or an executable check) · **check** = carried by a named executable check, not a card line · **partial** = only the stated part is carried · **GAP** = carried nowhere known; reviewer to rule.

| # | source | MUST | BOOTSTRAP | FIXTURE_BUILDER | FIXTURE_VERIFIER | OWNER_SURROGATE |
|---|---|---|---|---|---|---|
| 1 | §I B.1 | Facts at Gaṇita; derivations at the Bodha boundary with a ledger; interpretation above only | N/A — builds control-plane scripts; emits no chart fact or interpretation | partial FB-11 (cite `fact_id`, never re-derive); layer-separation rule → packet | partial FV-16 (same clause); remainder → packet | N/A — rules on owner-waits; makes no chart claim |
| 2 | §I B.3 | Every claim above Gaṇita lists the fact ids it consumes; no unsourced "classically known" | N/A — as row 1 | partial FB-11 (`fact_id` citation); ledger form → packet | partial FV-16; ledger form → packet | N/A — as row 1 (analogue: `evidence` in OS-18) |
| 3 | §I B.8 | Canonical artifacts carry version, status, changelog; registries agree | BS-14 | FB-11 | FV-16 | OS-14 |
| 4 | §I B.10 | No fabricated computation; never invent chart values | BS-13 | FB-12 | FV-16, FV-17 | OS-03 |
| 5 | §I B.11 | Interpretive queries route through Bodha synthesis first | N/A — answers no interpretive query; no chart data (no MCP, BS-18) | N/A — answers no interpretive query | N/A — answers no interpretive query | N/A — answers no interpretive query |
| 6 | §I Scope | Declare what you may / must not touch before editing; respect other campaigns' `must_not_touch` | BS-04, BS-05, BS-06, BS-07 | FB-08, FB-09 | FV-07, FV-08, FV-16 | OS-02, OS-07, OS-09 |
| 7 | §I Isolation | Never build or commit in the shared checkout; worktree + PR | BS-01, BS-08, BS-19, BS-20 | FB-07, FB-14, FB-16 | FV-07 (commits nothing) | OS-09 (nothing in the shared checkout), OS-17; a `_PROPOSED` plan file can take effect only through OS-14's activation record, which requires independently reviewed immutable source (plan pairing rule) — the card names no branch for it |
| 8 | §N.1 | External layer names only; never "L0–L5" externally | BS-15 | FB-13 | FV-16 | N/A — writes decisions, no layer-facing output (card text uses external names only) |
| 9 | §N.1 | Asset ids use underscore prefixes; dot-notation retired | BS-15 | FB-13 | FV-16 | N/A — creates no asset id |
| 10 | §N.2 | Writer is a `@register` `WriterBase` subclass with `run` or `plan_substeps` + `run_substep` | N/A — builds no writer; writers lie outside every bootstrap packet's paths (BS-06) | FB-11 | partial FV-16 (`@register` `WriterBase`; entry points not named) | N/A — builds nothing |
| 11 | §N.2 | Runs on `ctx.db_conn`; never commits or closes it | N/A — as row 10 | FB-11 | FV-16 | N/A — builds nothing |
| 12 | §N.2 | Never writes `asset_throughput` | N/A — as row 10 | FB-11 | FV-16 | N/A — builds nothing |
| 13 | §N.2 | `chart_id` + `birth_params` from `ctx.config` | N/A — as row 10 | FB-11 | FV-16 | N/A — builds nothing |
| 14 | §N.2 | A needed contract change → STOP, raise with the native | BS-05 | FB-09 | FV-16 (FROZEN path in a diff is a finding) | OS-07, OS-09 |
| 15 | §N.3 | Brahmagyan `ON CONFLICT` on global reference tables; other layers per-chart delete-then-insert | N/A — writes no layer table (BS-06) | partial FB-11 (delete-then-insert); Brahmagyan clause → packet | partial FV-16; Brahmagyan clause → packet | N/A — builds nothing |
| 16 | §N.4 | Floors are aspirational; never fabricate rows | BS-13 | FB-11 | FV-16 | OS-03 |
| 17 | §N.4 | No audience tier in writers | N/A — builds no writer | FB-11 | FV-16 | N/A — builds nothing |
| 18 | §N.4 | Deterministic-first: Python over LLM for computation | BS-11 | FB-11 | FV-16 | N/A — computes nothing; rules on evidence it inspects (OS-03) |
| 19 | §N.4 | No JH-parity oracle | N/A — verifies no chart computation | FB-11 | FV-16 | N/A — verifies no chart computation |
| 20 | §N.4 | Cockpit truth: chart-scoped `count_sql` on `asset_registry` | N/A — registers no asset | packet — only if a fixture item registers an asset | packet — as FB | N/A — registers no asset |
| 21 | §N.4 | Surgical migrations, verified applied; never edit an applied migration | BS-06 (migrations out of scope unless enumerated) | partial FB-11 (allocated number; no edit of an applied file); "verify applied" is the readback job's (plan §6), builder has no production access | FV-16 | OS-05, OS-08 (a protected window is veto-class; the platform approval stays human) |
| 22 | §N.4 | Honest verification tiers via `verification_vocab.py` constants; never `two_pass_verified` unearned | N/A — emits no chart-row tier (general rule BS-12) | FB-11 | partial FV-16 (constants; unearned tier via "detector that can fail") | N/A — emits no tier (analogue OS-03) |
| 23 | §N.5 | Reference the Gaṇita `fact_id`, inherit its value; a disagreement is a halt-worthy bug; MSR constituent facts resolve | N/A — consumes no chart fact | partial FB-11; MSR-resolution clause → packet | partial FV-16; MSR clause → packet | N/A — consumes no chart fact |
| 24 | §N.6 | Serving density (1–4): catalog ≠ confirmed; `hardFloor`; verdict layer never empty; `density_contract` | N/A — builds no served surface | packet — only if a fixture item touches a served surface | packet — as FB | N/A — builds no served surface |
| 25 | §N.7.1 | Narration restates a cited `fact_id`; never re-derives | N/A — writes no narration | FB-11 | FV-16 | N/A — writes no narration |
| 26 | §N.7.2 | Single-row selection pins `fact_key` with a total `ORDER BY` | N/A — writes no selector | check — CI guard `check_fact_category_pinning.py`; no card line | check — same guard; no card line | N/A — writes no selector |
| 27 | §N.7.3 | No wrapper-local constant shadows a Gaṇita value | N/A — holds no chart value | FB-11 ("never restate") | FV-16 ("value never restated") | N/A — holds no chart value |
| 28 | §N.7.4 | A verification flag has a real detector, or is null | BS-12 | FB-12 | FV-16 | OS-03 |
| 29 | §N.7.5 | Each narration layer has its own semantic / golden-value test | N/A — writes no narration | packet — only if a fixture item adds narration | packet — as FB | N/A — writes no narration |
| 30 | §N.7.6 | An honest null beats an invented judgment | BS-13, BS-23 | FB-12, FB-18 | FV-15, FV-17, FV-21 | OS-03, OS-20 |
| 31 | §N.8 | Every status, grade or PASS is computed by a detector that can fail; else null | BS-12, BS-10, BS-24 | FB-12, FB-10 | FV-14, FV-15, FV-16, FV-17 | OS-03 (no pass without proof), OS-06 (a failed notification prevents effectiveness) |
| 32 | D-1 | Control-plane changes only in Wave B, scoped per packet | BS-03, BS-04 | FB-09 (prohibited to this role) | FV-16 (control-plane code in a diff is a finding) | OS-02 (cannot alter D-1) |
| 33 | D-1 | Independently reviewed | BS-03, BS-21 | N/A — makes no control-plane change (FB-09) | N/A — reviews fixture items only | OS-10 |
| 34 | D-1 | Installed with a receipt | BS-03, BS-07, BS-23 (never installs; never edits installed trees; reports the exact head) | N/A — as row 33; FB-09 | N/A — FV-08 | OS-12 |
| 35 | D-1 | Campaign builders keep the prohibition | BS-03 | FB-09 | FV-16 | OS-02 |
| 36 | D-6 revised | No PR merges to main during the certification hold; a merge authorisation is a durable local request, executed after certification-done, recorded with its actual workflow outcome | BS-21, BS-23 | FB-15, FB-03 (no real merge request) | FV-18 | OS-11 |
| 37 | D-9 | Installation uses the independently accepted immutable head bound in the receipt; no merge needed in Wave B | BS-03, BS-23 | N/A — fixture items are never installed | N/A — as FB (analogue FV-12: one registered head) | OS-12 |
| 38 | KV-08 | The GitHub protected-environment approval is a human act: authorise the bounded request only; record it as an external approval dependency; no veto deadline substitutes for it | BS-17 (no protected-window dispatch) | FB-03 | FV-03 | OS-07, OS-08 |
| 39 | KW-02 | Child jobs take no role lock and write no role-state file; they return results | BS-02, BS-22 | FB-07, FB-17 | FV-11, FV-20 | OS-20 |
| 40 | §3 Kept | COVERAGE: binding rules carried in the card, never by reference | this table; no card line cites CLAUDE.md in place of a rule | same | same | same (OS-09 names the sections and states the boundaries) |
| 41 | §3 Kept | FROZEN manifest; conforming new writers permitted; a frozen change is STOP for native authorisation | BS-05 | FB-09, FB-11 | FV-16 | OS-07 |
| 42 | §3 Kept | Tracker is the only ledger; typed guarded completion; verdict identity | N/A — BS-02: the live tracker does not know `KV3-B-*` items; the result file is the report | FB-15, FB-16 (fixture tracker) | FV-12, FV-18, FV-19 | OS-19 (routine `ky decide`), OS-05 (nothing published for a veto class) |
| 43 | §3 Kept | Independent verifier runs the tests itself; builder results are inputs | BS-10, BS-21 | FB-15 | FV-11, FV-14 | OS-10 |
| 44 | §3 Kept | Required CI checks; `Kāla DB Tests` — absent, skipped or failed is not success | no card line — enforced at review and at merge authorisation (OS-10) | FB-10 (`precheck.sh`); DB evidence judged by the verifier | FV-15 | partial OS-10 (required checks green; `Kāla DB Tests` not named) |
| 45 | §3 Kept | Semantic acceptance obligations of retained items | BS-09, BS-10, BS-24 (packet's expected result and negative cases) | FB-10 | FV-14, FV-17 | OS-03 |
| 46 | §3 Kept | Protected-window flow is an owner-approved GitHub action | BS-17 | FB-03 | FV-03 | OS-05, OS-07, OS-08 |
| 47 | §3 Kept | Executor operations: request-bound pre-acceptance, backup/restore/dry-run, quiescence evidence | BS-17 (no executor submission) | FB-03 (none outside the fixture backend) | FV-03 | N/A — owned by PRE-ACCEPT / EXECUTE jobs; OS-03 forbids waiving evidence; OS-07 hard-stops production deletion/restore |
| 48 | §3 Kept | Migration allocation | N/A — BS-06: migrations out of scope unless the packet enumerates them | FB-11 | FV-16 | N/A — allocates nothing |
| 49 | §3 Kept | No worker holds `DATABASE_URL` | BS-16 | FB-06 | FV-06 | partial OS-08 (credentials; `DATABASE_URL` not named) |
| 50 | §3 Kept | No model merges or dispatches production | BS-21, BS-17 | FB-15, FB-03 | FV-18 | OS-08, OS-11 (authorises; nothing merges during the hold) — plan §3 wording vs D-5 flagged to the reviewer |
| 51 | §3 Kept | Routing by rule; escalation grants no authority | N/A — model fixed by the roster | N/A — routing is the dispatcher's script; the same card binds whichever model runs | N/A — as FB | N/A — not a routed role |
| 52 | §3 Kept | One governance record pair (C-2 banner + SESSION_LOG entry; C-4 close) | N/A — written by the planner (B-5) and `finalize.sh`; BS-20 forbids ledger PRs | N/A — as BS; FB-14 | N/A — writes no governance record | N/A — writes no governance record |

GAP cells: none. The three of the previous draft are closed by card lines — row 3 (FB-11, FV-16 now carry the versioning clause), row 7 (OS-09, OS-14) and row 48 (FV-16 now checks the allocated migration number).
