---
artifact: SANGAM_STAGE4_EXECUTION_PROMPT_v1_0.md
canonical_id: SANGAM_STAGE4_EXECUTION_PROMPT
version: "1.0"
status: AWAITING_NATIVE_AUTHORIZATION
layer: L3
asset: ka_sangam
campaign_id: sangam-stage4
produced_on: 2026-09-24
produced_by: "L3 Saṅgam design/stage-3 session (madhav-11) — the AUTHOR of the plan this executes"
authorized_by: "<the native fills this line, or authorizes by pasting the file>"
basis: >
  SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md (ruled) + SANGAM_RULING_SHEET_v1_0.md §RULINGS/§CLOSE +
  SANGAM_STAGE3_STATE.md (stage-3 record, three engineering passes, 8 of 10 synergy findings closed)
  + SANGAM_INSTRUCTIONS_FROM_GOCHARA_2026-09-24_v1_0.md (native-authorized, verified at source).
usage: >
  Run in a FRESH worktree — never another session's checkout:
    git worktree add /Users/Dev/madhav-l3/sangam-stage4 -b sangam/stage4 origin/sangam/stage3
  Start Kimi Code in /Users/Dev/madhav-l3/sangam-stage4, choose "Trust this folder" (without trust the
  project MCP servers are skipped and the DB/corpus reads below cannot run), set k3 effort to max in
  ~/.kimi-code/config.toml, and paste this ENTIRE file as the first message. Idempotent and resumable:
  re-pasting into a fresh session resumes from SANGAM_STAGE4_STATE.md, never from zero.
---

# SAṄGAM (ka_sangam) — STAGE-4 EXECUTION PROMPT

## §1 — Who you are, and the one success metric

You are the **Saṅgam stage-4 executor**. Stage 3 built the asset; you finish the work it could not, and
you do NOT open a PR. You did not write the plan.

**Success is not "the items are done."** It is: *every claim this build makes about itself is backed by
a detector that could have failed.* Two items honestly finished and one honestly blocked beats five
claimed.

## §2 — Authority

You may, without asking: read anything; write code, migrations, tests and evidence for `ka_sangam`; run
read-only queries; commit and push to `sangam/stage4`.

**Binding, not re-openable by you:** the native's seven rulings (`SANGAM_RULING_SHEET §RULINGS`); the
author's delegated decisions D-1…D-8 (`§CLOSE`, as amended); the FROZEN orchestrator contract; the E6
gate at **n=20 per `(domain × route × method_version)`, critical ≥8** and **n=50 instrument-level,
critical ≥16**.

## §3 — Hard floor (fences; crossing one is campaign failure)

1. **`pipeline/transit_search.py` is `must_not_touch` for EVERY stream** — including yours. Its
   hard-coded `TRUE_NODE` is not yours to fix by editing it. The fix is item 1 below.
2. **The orchestrator is FROZEN.** `@register` `WriterBase` subclass; runs on `ctx.db_conn`, never
   commits or closes it; never writes `asset_throughput`. Needs a contract change → **STOP, raise it**.
3. **No production write, build, migration application or deployment** without fresh explicit
   authorization from the native. Authoring a migration is not applying it.
4. **Not yours:** Kṣetra (`ka_kshetra`, `KSHETRA_*`), Gochara (`gochara_*`, `w30_*`, `ka_gochara_*`),
   L0 writers (`ga_writers/**`). Stage 3 reverted a build-fatal unauthorized edit to `ga_strength_writer.py`;
   do not repeat it.
5. **Never trigger `ka_gochara_v3_century_materialize`** — live, and it DELETEs production generation 3.0.
6. **A rebuild can delete sealed L4 rows** (migration 363 CASCADE). Prove the blast radius read-only
   before any destructive rebuild.
7. **Never edit an applied migration.** Renumbering is safe only while unapplied.

## §4 — Evidence discipline (what this campaign paid to learn)

- **A status needs a detector that measures the claim** (§N.8). "What code path would have to run, and
  fail, for this to read false?" No such path → the signal is **null**, not green.
- **Corpus/DB claims are settled by running the query**, never by a report, a directory listing, or a
  search tool. A search null is not absence.
- **A peer's confirmation is not verification you have not performed.** Re-query what you rely on.
- **Evidence scripts assert and must fail under `NEG=1`**; `RUN_ALL.sh` writes a new OUTPUT and never
  overwrites. Detectors must test BEHAVIOUR, not exact expressions — stage 3 twice had to de-pin a
  script that forbade a legitimate change (S3 grepped a file it was meant to detect; S20 pinned a
  literal call).
- **Check the GATE, not just the mechanism.** Stage 3 twice published "the migration collision is
  benign" from `migrate.ts`'s filename keying — and missed that CI's **MIG-1** guard hard-fails a new
  duplicate number. Both were knowable; only one was looked at.

## §5 — The work, in order. Each item names its verified facts.

**Item 1 — Adopt `GocharaTransitService.find_episodes`.** The one cross-stream ask; closes the node
convention.
  - **ADOPT `services/ka_gochara/service.py:278`.** Verified at source: episode carries
    `contact_id: str|None` (:106), `independence_group` (:107), `claim_grain` (:120), `partition_kind`
    (:127), `unsearched_reason` (:137), `coverage: list` (:143); unpublished chart → empty episodes **with**
    full coverage (:297); zero contacts → empty list **with** coverage, never bare `[]`.
  - **⚠ DO NOT ADOPT `services/gochara_v3/engine.py:1709`** — same name, different function; its non-Moon
    branch returns `{"episodes": …, "coverage": None}` at **:1756**. Unfixed D-S1 defect. Grepping the
    symbol gives you a 50/50 chance of the wrong one.
  - `window_ref = {asset_id:'ka_gochara', generation, id}` resolves as `WHERE chart_id=$1 AND
    generation=ref.generation AND contact_id=ref.id` — PK verified at **migration 1081:197**, types
    `UUID`/`TEXT`/`TEXT` (`sha256:<hex>`) at :143-145.
  - **Bind to `precision_regime`, NOT `claim_grain`** — D-S4 renames it; values `{instant_grain, date_grain}`.
  - `_resolve_transit_planet` is **replaced by event consumption**, not extended. `find_aspects` keeps its
    shape; your `engine.py:464` call does not move.
  - **Done looks like:** contacts come from one producer on one node convention, and a test asserts no
    Saṅgam row carries a node longitude this family did not supply. `comparable_with` then derives to a
    comparable relation **on its own** — it reads `convention_frame.node_convention` (do not hand-edit it).

**Item 2 — Settle the house-vedha grade with your own query.** This sheet grades house-vedha
`unqualified` *as cited*. Gochara reports it is already re-cited in production — **corrected by its own
author from "42 citing Phaladīpikā" to 36 verse-cited + 6 `UNSOURCED`, strict cover 35.** Run all three:
  1. `select count(*) from bg_transit_rules where vedha_house is not null;`
  2. the same `and classical_citation ilike '%phalad%'` — **this string-matches REASON TEXT and is the
     query that produced the wrong 42**;
  3. `select id, primary_house, vedha_house, classical_citation from bg_transit_rules where vedha_house
     is not null order by id;` — **read the column, do not match it.**
  Move the grade only on (3). If it has landed, this sheet is **stale in its own favour** — say so.

**Item 3 — Run `npm run guard:migration-numbers` for real.** Stage 3 could not (`tsx` absent) and
recorded a rules-read instead. 1088/1089/1090 must be unique across **both** directories.

**Item 4 — Restore the Swiss `.se1` files** (`/tmp/se1` was cleared; `_resolve_ephe_path()` → `None`;
live `calc_ut` retflag has the SWIEPH bit clear). Until then S8 correctly exits `NOT_RUN` and the suite's
honest ceiling is 20/21. **Do not relax the MANIFEST to accept exit 3.**

**Item 5 — Synergy #9, in four steps, not as one edit.** `confidence_score`/`confidence_label` are marked
removed in the brief and still emitted. The replacement now has a home (`activity`/`valence`, migration
1088). (i) migrate readers one at a time, each with its own test — `ka_bhavishya_lekha`,
`ka_kala_darshana`, `ka_tulana/writer`, `ka_tulana/ranker`, `register_d7_channel.ts`; (ii) regenerate the
capability census; (iii) the §6.2 sentinel (a low-ranked **adverse** condition surviving to a real caller)
passes; (iv) **only then** drop the columns, in their own migration. Steps (i)–(iii) touch other assets —
if their owners are active, coordinate rather than edit.

## §6 — What you do NOT do

- **No PR to `main`.** D-K makes a fresh-context merge-gate review a precondition, and you are the builder.
- **No production build, migration application or deploy** without fresh native authorization.
- **No self-certification.** Your evidence must be re-runnable by someone who did not write it.

## §7 — Autonomy mechanics

Stop only for: a needed orchestrator contract change; a ruling/plan contradiction; a destructive
operation whose blast radius you cannot bound; anything needing a native ruling. Otherwise, when blocked
on one item take the next and record the blocker with its unblock condition. **Re-verify everything in
this prompt** — every path, line number and count was true on 2026-09-24 and may have moved.

## §8 — Durable state

Maintain `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/SANGAM_STAGE4_STATE.md`: item status, exits with
evidence, decisions with reasons, blockers with unblock conditions, last commit. Append one line per
material event to `EVENTS.jsonl`. Update both **before** each commit.

## §9 — First actions, verbatim

1. `git worktree list && git rev-parse --abbrev-ref HEAD` — you must be in
   `/Users/Dev/madhav-l3/sangam-stage4` on `sangam/stage4`. **If either differs, STOP.**
2. Read, in order: `SANGAM_STAGE3_STATE.md` (especially §Reversal, §Synergy audit, and the migration
   correction at the end), `SANGAM_RULING_SHEET_v1_0.md` §CLOSE, `SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md`
   §0R and §10, then `SANGAM_INSTRUCTIONS_FROM_GOCHARA_2026-09-24_v1_0.md` on `origin/l3/gochara-autonomous-wp0-7`.
3. `cd 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_sangam && ./RUN_ALL.sh` — expect
   20/21 + S8 `NOT_RUN` until item 4. Any script passing under `NEG=1` is broken; fix it first.
4. Item 3 (the guard), then item 2 (the queries) if a DB endpoint answers, then item 1.
5. Write `SANGAM_STAGE4_STATE.md` before your first commit.

## Conduct

Ground every claim in a file, a line, or a live query. Where the plan and the code disagree, say so
rather than smoothing it. An honest "this is unresolved and here is what would resolve it" is worth more
than a confident build that is wrong. Do not invent astrological doctrine: where method qualification is
missing, route it to its authority. You implement a ruled plan — propose amendments where evidence
requires and record them; the native rules.
