# M0-T64 — import-blast-radius triage of the unguarded top-level `main()` population

**Agent:** KĀRAKA-M0-T64 · **Task:** `WORK_QUEUE` `M0-T64` · **Authority:** ruling **D-67 part 2**
**Branch:** `campaign/nirmana-autonomous` · **Written:** 2026-08-23T16:23:12Z
**Machine-usable output:** `00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json` (tracked)

**This is an observation report, not a verdict. I do not certify my own work (I16/H7).**
**I repaired nothing. Not one file in the population was edited.**

---

## 1 — The three things that matter, up front

1. **TIER 1 IS LARGE: 58 of 76.** D-67 says in terms: *"If the triage finds tier 1 is large,
   that is a finding to bring me, not a reason to widen the grant unasked."* So this report
   stops at the measurement. **No tier-1 repair was begun, and none should be dispatched as a
   single task.** §7 is the finding, routed to ADHIKĀRIN.
2. **MY POPULATION IS 76, NOT 81.** I re-derived it rather than accepting it, as instructed, and
   I cannot reproduce 84/81 with any pattern I tried. §2 shows every command and every number.
   The gap is not a rounding difference — it is 5 files, and there are exactly 5 already-guarded
   files that are neither of the three `isDirectEntrypoint` repairs nor the two `IMPORT_ONLY`
   gates. That is a plausible explanation but I did not confirm it, so I report the discrepancy
   as a discrepancy.
3. **`platform/scripts` IS EXCLUDED FROM THE TYPESCRIPT PROJECT** (`platform/tsconfig.json`
   `"exclude": ["node_modules", "scripts"]`). The whole population sits outside `tsc --noEmit`.
   That is why **9 of the 76 import modules that do not exist on disk** and nothing has ever
   said so. §6.

---

## 2 — The population, re-derived (D-67 part 1 asked for this to be re-derived, not accepted)

Every command below was run; every number is its output.

```
$ git ls-files platform/scripts | grep -c '\.ts$'
213                                     # tracked .ts files under platform/scripts
$ git status --porcelain platform/scripts
(empty)                                 # no untracked .ts to miss
```

Two candidate definitions of "top-level `main()` call", and they differ:

```
# (A) start-of-line at ANY indentation — includes calls inside a guard block
$ git grep -lP "^\s*(void\s+|await\s+)?main\s*\(" -- platform/scripts | grep -c '\.ts$'
86

# (B) column 0 — a genuinely unguarded module-top-level call
$ git grep -lP "^(void\s+|await\s+)?main\s*\("   -- platform/scripts | grep -c '\.ts$'
76
```

**86 − 76 = 10, and all ten are genuinely guarded.** I read every one:

| file | guard | line |
|---|---|---|
| `scripts/migrate.ts` | `isDirectEntrypoint(...)` | 1002 |
| `scripts/seed/asset_registry_seed.ts` | `isDirectEntrypoint(...)` | 3752 |
| `scripts/pariprashna/ledger_writer_worker.ts` | `isDirectEntrypoint(...)` (M0-T60) | 225 |
| `scripts/ci/dispatch_gate.ts` | `IMPORT_ONLY !== '1'` (M0-T50) | 194 |
| `scripts/ci/verify_migrations_deployed.ts` | `IMPORT_ONLY !== '1'` (M0-T50) | 253 |
| `scripts/census/shad_darshana_gates/citation_verify_gate.ts` | `process.argv[1] && /citation_verify_gate\.(ts\|…)$/.test(...)` | 270 |
| `scripts/census/shad_darshana_gates/completeness_census_seed.ts` | same argv-regex idiom | 687 |
| `scripts/census/shad_darshana_gates/specificity_gate_v0.ts` | same argv-regex idiom | 564 |
| `scripts/generate_vidhi_registry_mirror.ts` | `if (isEntrypoint)` | 266 |
| `scripts/governance/icr_pr_gate.ts` | `if (isMain)` (argv `.endsWith`) | 276 |

I also checked that none of the 76 has a guard on the line above its call (`if` / `require.main`
/ `argv` scan over line *n−1*): **zero hits**. And the 76 matches are all real call sites — I
printed all 76 with line numbers and read them; the forms are
`main().catch((err) => {` ×33, `main()` ×17, `main().catch(err => {` ×13, plus five one-offs.

**Patterns I tried and the counts they give** (none is 84):

| pattern (over `platform/scripts`, `.ts` only) | count |
|---|---|
| `^\s*(void\s+)?main\s*\(` | 86 |
| `^\s*(void\s+\|await\s+)?main\s*\(\)` | 86 |
| `^\s*(void\s+\|await\s+)?(main\|run\|cli)\s*\(` | 86 |
| `^(void\s+)?main\s*\(` | **76** |
| the same start-of-line form repo-wide (not scoped to `platform/scripts`) | 112 |

**So: the guarded population is 10, not 3, and the unguarded population is 76, not 81.**
`86 − 2` is 84, which would be reached by a scan that excluded the two `IMPORT_ONLY` gates — but
that is my speculation about someone else's command, not a measurement, and I flag it as such.

**Exclusions applied to every scan** (per the caution about prose that documents code):
pathspec limited to `platform/scripts`, so no markdown, no `00_ARCHITECTURE/**` prose, no
`99_ARCHIVE/**`; filtered to `*.ts`; and **every property detector ran over source with `//` and
`/* */` comments blanked out first**, so a commented-out or documented form cannot produce a hit.
String and template-literal bodies were deliberately **not** blanked — SQL only ever appears
inside a string, so blanking them would blind the (b) database detector — and to keep that honest
I read all 26 database-write hits individually (§4.2). None is prose.

One file is in the population despite its path and I flag it rather than silently dropping it:
`platform/scripts/_archived/seed-abhisek.ts`. It is under an `_archived/` directory but is a live
tracked `.ts` matching the definition, and it is tier 1.

---

## 3 — The method, and the one measurement that made it tractable

D-67's criterion is about **incidental import**. The population's defining property is that
`main()` is called at module top level with no guard — so **importing the file executes the
program**. That means (a), (b) and (c) are properties of the *program*, not only of its
module-scope statements, and a scan that only looked at top-level statements would grade almost
everything tier 3 and be wrong.

It also raises the opposite worry: if effects can arrive through the import graph, then a file's
tier depends on ~200 other modules. So I measured that directly, over the full transitive
internal import graph of each of the 76 (resolving `@/*` → `platform/src/*` and relative
specifiers; graphs range from 1 to 228 modules):

> **No module in any of the 76 import graphs performs a credential acquisition, connection open,
> filesystem write, network call or `process.exit` at its own module scope.** Files with any
> dependency module-scope effect: **0**.

The two shared DB helpers are lazy by construction and I read them to confirm:
`platform/src/lib/db/client.ts` builds its `Pool` inside `initPool()`/`getPool()` (lines 44–75),
`platform/scripts/harvest/_db.ts` inside `openHarvestClient()` (line 52), and
`platform/scripts/audit/tap/lib/tap_db.ts` dynamically imports the client inside `connectTapDb()`
(line 46+). So **every effect in this triage is reached through the entry file's own `main()`** —
which is exactly the T60 shape, and it means a per-file determination is a real determination
rather than a guess about a graph.

Determination rule, stated so the JSON can be audited against it:

- **(a) YES — direct**: the entry file itself constructs a `Pool`/`Client`, calls `getPool`,
  reads a credential-shaped env var, calls `fetch`, initialises `firebase-admin`, builds an MCP
  client, or `execSync`s a credential fetch.
- **(a) YES — via helper**: `main()` calls a named helper that does one of those. Each of these
  20 was established **by reading `main()`**, and the helper and its line are in the evidence
  field. Not inferred from the graph.
- **(a) NO — adjudicated**: I read `main()` and its call path and it touches only in-memory
  structures, `fs` reads, or source scanning. 18 files; the reason is recorded per file.
- **(a) UNDETERMINED**: reserved for what I could not settle. **It is empty, and I want to be
  explicit that this is a claim, not an absence of effort** — §8.1 states what it does not cover.

`getCatalog()` / `getAllCapabilities()` deserve a note because five files rest on them: both are
`Array.from(_registry.values())` (`platform/src/lib/retrieval/registry/index.ts:110,133`;
`registry/catalog.ts:128`), i.e. in-memory reads of an already-registered catalogue. Registration
is a module-scope effect of ~200 modules, but the module-scope scan above says none of those
registrations connects, writes or exits. That is why those five are graded (a) NO and not
UNDETERMINED.

---

## 4 — The result

| | count | share |
|---|---|---|
| **TIER 1** — (a) or (c) | **58** | 76% |
| **TIER 2** — (b) alone | **6** | 8% |
| **TIER 3** — neither | **12** | 16% |
| **UNDETERMINED** | **0** | — |

Tier 1 broken down by *which* property put it there:

| because | count |
|---|---|
| **(a) and (c)** — opens/acquires **and** kills the importer | **44** |
| **(c) alone** — inert otherwise, but `process.exit` kills the importer | **9** |
| **(a) alone** — opens/acquires, does not exit | **5** |

Property totals: (a) YES **49** · (b) YES **30** (filesystem 17, database 9, network 9;
files may write more than one kind, so these do not sum to 30) · (c) YES **53**.

### 4.1 — The 9 "tier 3 only because it cannot load" files — read §6 before trusting this row

9 of the 12 tier-3 files are tier 3 **for a reason that is not safety**: a static import
specifier that resolves to no file on disk. Under ESM every static import is linked before the
module body runs, so the body — and its `main()` call — never executes. **All 9 would be TIER 1
if the missing module were restored**, and 2 of them construct a credentialed `Pool` and run
`INSERT`s. They are recorded with `tier_if_import_resolved: 1` and a `tier_note` saying so, so
nobody can read the tier-3 count as "12 harmless scripts". The genuinely inert count is **3**.

### 4.2 — Every database-write hit, read individually (no false positives)

26 hits across 10 files, all real SQL in real query strings (9 of the 10 are graded (b) YES;
`bootstrap/bootstrap_classical_texts_tajaka.ts` is not, because it cannot load — §6): `_archived/seed-abhisek.ts` (4
`INSERT`, 2 `ON CONFLICT`), `audit/smoke.ts` (2 `INSERT` incl. `prediction_ledger`),
`backfill_conversation_embeddings.ts`, `bootstrap/bootstrap_classical_texts_tajaka.ts`,
`bootstrap/bootstrap_multi_school_tajaka.ts`, `corpus/apply_muhurta_chintamani_translations.ts`
(2 `UPDATE classical_text_chunks`), `dedupe_charts.ts` (`DELETE FROM charts`),
`governance/seed_tool_registry.ts`, `probe/ask.ts` (`UPDATE conversations`),
`probe/dd16_outbox_recovery_test.ts` (`DELETE FROM pariprashna_persistence_outbox`).


### TIER 1 — 58 files

| file (under `platform/scripts/`) | (a) cred/conn | (b) write | (c) exit | tier-1 by |
|---|---|---|---|---|
| `_archived/seed-abhisek.ts` | YES | YES/d | YES | a+c |
| `aiops/cutover_smoke.ts` | NO | YES/f | YES | c |
| `answer_eval.ts` | YES | YES/n | YES | a+c |
| `audit/alias_conformance_check.ts` | YES | NO | YES | a+c |
| `audit/density_harness/run.ts` | NO | NO | YES | c |
| `audit/doctrine_harness/run.ts` | YES | NO | YES | a+c |
| `audit/doctrine_harness/run_census.ts` | YES | NO | YES | a+c |
| `audit/doctrine_harness/run_master_gate.ts` | YES | NO | YES | a+c |
| `audit/replay.ts` | YES | NO | YES | a+c |
| `audit/smoke.ts` | YES | YES/d | YES | a+c |
| `audit/t0_retrodiction/fetch_populated_event_classes.ts` | YES | YES/f | YES | a+c |
| `audit/t0_retrodiction/run_a5_dry_run.ts` | YES | NO | YES | a+c |
| `audit/t0_retrodiction/run_t0.ts` | YES | NO | YES | a+c |
| `audit/tap/mcp_tool_smoke.ts` | YES | YES/n | YES | a+c |
| `audit/tap/r18_param_noop_audit.ts` | NO | NO | YES | c |
| `audit/tap/s13_coverage_matrix_live.ts` | YES | NO | YES | a+c |
| `audit/tap/tap5_seam_conservation.ts` | YES | NO | YES | a+c |
| `audit/tap/tap6_method_grep.ts` | NO | NO | YES | c |
| `audit/tap/tap7_distribution_gates.ts` | YES | NO | YES | a+c |
| `backfill_conversation_embeddings.ts` | YES | YES/d,n | YES | a+c |
| `bootstrap/bootstrap_multi_school_tajaka.ts` | YES | YES/d | YES | a+c |
| `census/elev_gates/budget_census_gate.ts` | YES* | NO | YES | a+c |
| `census/elev_gates/receipt_gate.ts` | YES* | NO | NO | a |
| `census/elev_gates/smoke_gate.ts` | YES* | NO | NO | a |
| `census/elev_gates/w1_bare_empty_census_gate.ts` | YES* | NO | YES | a+c |
| `census/generate_tci.ts` | YES | YES/f | YES | a+c |
| `census/rescan_dark_tables_widened_surface.ts` | NO | YES/f | YES | c |
| `census/shad_darshana_gates/authority_basis_census_seed.ts` | NO | NO | YES | c |
| `census/shad_darshana_gates/mode3_single_route_gate.ts` | YES* | NO | YES | a+c |
| `census/shad_darshana_gates/tri_plane_no_dead_end_gate.ts` | YES* | NO | YES | a+c |
| `census/shad_darshana_gates/yajna_mode2_fixture_gate.ts` | YES* | NO | YES | a+c |
| `cleanup_orphaned_firebase_users.ts` | YES | NO | YES | a+c |
| `corpus/apply_muhurta_chintamani_translations.ts` | YES | YES/d,n | YES | a+c |
| `cutover/stage1_smoke.ts` | YES | YES/n | YES | a+c |
| `dedupe_charts.ts` | YES | YES/d | YES | a+c |
| `dev/mint_session_cookie.ts` | YES | YES/f,n | YES | a+c |
| `diag/check_signal.ts` | YES | NO | YES | a+c |
| `gochara/smoke_probe.ts` | YES | YES/n | YES | a+c |
| `governance/run_icr_propose_patch.ts` | NO | YES/f | YES | c |
| `governance/seed_tool_registry.ts` | YES | YES/d | YES | a+c |
| `grounding/grounding_review_queue.ts` | NO | YES/f | YES | c |
| `harvest/e2_db_truth_extractor.ts` | YES | YES/f | YES | a+c |
| `harvest/e3_fact_category_extractor.ts` | YES | YES/f | YES | a+c |
| `harvest/e4_signal_class_extractor.ts` | YES | NO | NO | a |
| `harvest/load_harvest_to_ledger.ts` | YES | NO | YES | a+c |
| `manifest/generate_concept_projections.ts` | YES | YES/f | YES | a+c |
| `nim_one_shot_planner.ts` | NO | NO | YES | c |
| `observatory/smoke_test.ts` | YES | NO | YES | a+c |
| `pariprashna/verify_captured_turn.ts` | YES | NO | YES | a+c |
| `probe/ask.ts` | YES | YES/f,d,n | YES | a+c |
| `probe/dd16_outbox_recovery_test.ts` | YES | YES/d | NO | a |
| `probe/dd20_e2e_verify.ts` | YES | NO | NO | a |
| `replay/selftest.ts` | YES | NO | YES | a+c |
| `retrieval/probe_11c_b.ts` | YES | YES/n | YES | a+c |
| `samiksha/daily_job.ts` | YES | NO | YES | a+c |
| `set-password.ts` | YES | NO | YES | a+c |
| `trace/trace_smoke.ts` | YES | NO | YES | a+c |
| `verify_classical_texts_data.ts` | YES | NO | YES | a+c |

### TIER 2 — 6 files

| file (under `platform/scripts/`) | (a) cred/conn | (b) write | (c) exit | tier-1 by |
|---|---|---|---|---|
| `audit/capability_map/generate_capability_map.ts` | NO | YES/f | NO |  |
| `census/generate_tool_census.ts` | NO | YES/f | NO |  |
| `harvest/cross_diff_adjudication.ts` | NO | YES/f | NO |  |
| `harvest/e1_registry_extractor.ts` | NO | YES/f | NO |  |
| `manifest/generate_projections.ts` | NO | YES/f | NO |  |
| `replay/build_fixtures.ts` | NO | YES/f | NO |  |

### TIER 3 — 12 files

| file (under `platform/scripts/`) | (a) cred/conn | (b) write | (c) exit | tier-1 by |
|---|---|---|---|---|
| `aiops/probe_health_cron.ts` | NO | NO | NO |  |
| `bootstrap/bootstrap_classical_texts_bphs.ts` | NO | NO | NO |  |
| `bootstrap/bootstrap_classical_texts_jaimini.ts` | NO | NO | NO |  |
| `bootstrap/bootstrap_classical_texts_kp.ts` | NO | NO | NO |  |
| `bootstrap/bootstrap_classical_texts_tajaka.ts` | NO | NO | NO |  |
| `census/elev_gates/absence_lint_gate.ts` | NO | NO | NO |  |
| `lint/no_hardcoded_concept_lists.ts` | NO | NO | NO |  |
| `manifest/backfill_descriptor_fields.ts` | NO | NO | NO |  |
| `retrieval/embedding_freshness_check.ts` | NO | NO | NO |  |
| `retrieval/test_classify.ts` | NO | NO | NO |  |
| `sla_probe_planner_blind_tools.ts` | NO | NO | NO |  |
| `sla_probe_temporal.ts` | NO | NO | NO |  |

`*` on (a) marks **conditional**: the connection is opened only in LIVE mode
(`MCP_SERVER_URL` set); with it unset the gate runs in PLAN mode and opens nothing. Seven gates
are in this class. I graded them (a) YES because the code path exists and the env var is set in
the pipeline the header documents; the conditionality is recorded per file as
`a_conditional_on_env: true` so a repair can treat them as their own sub-class.
`(b)` kinds: `f` filesystem, `d` database, `n` network.

---

## 5 — The five worst cases, named, because a count is not a hazard

Tier 1 is 58 files, but the tiers are not evenly severe inside themselves. These five are the
ones I would put in front of ADHIKĀRIN first, and the reason is T60's reason — what one import
in an ordinary shell would actually do:

| file | what importing it does |
|---|---|
| `probe/ask.ts` | `execSync('gcloud secrets versions access latest --secret=… --project=madhav-astrology')` (:164) and `execSync('firebase apps:sdkconfig WEB …')` (:185) — **shells out to fetch production secrets**; then `new Client`, `client.connect()`, `UPDATE conversations`, `writeFileSync`, `process.exit` |
| `dedupe_charts.ts` | credentialed `Pool`, `client.connect()`, **`DELETE FROM charts WHERE chart_id = $1`** |
| `_archived/seed-abhisek.ts` | credentialed `Pool` + `firebase-admin` + 4 `INSERT`s incl. `ON CONFLICT (id) DO UPDATE SET role='super_admin'` — under an `_archived/` path, which is exactly the kind of file an incidental import would be assumed harmless |
| `dev/mint_session_cookie.ts` | `firebase-admin` + credential env reads + `fetch` POST + `writeFileSync` — **mints a session cookie** |
| `set-password.ts` | `firebase-admin` + credential env reads; the name is the hazard |

`corpus/apply_muhurta_chintamani_translations.ts` (2 × `UPDATE classical_text_chunks`),
`governance/seed_tool_registry.ts` and `audit/smoke.ts` (`INSERT INTO prediction_ledger`) are the
next rank.

---

## 6 — A finding I did not go looking for: 9 scripts import modules that do not exist

While resolving import graphs I found specifiers that resolve to nothing on disk. I verified each
target's absence directly (`ls` of every candidate extension and `index.*`), and checked the repo
for a relocated copy.

| script | unresolvable specifier(s) | target |
|---|---|---|
| `bootstrap/bootstrap_classical_texts_bphs.ts` | `./lib/classical_text_chunker`, `./lib/classical_text_embedder` | `platform/scripts/bootstrap/lib/` contains only `tajaka_corpus.ts`; `git ls-files \| grep -c classical_text_embedder` → **0** |
| `bootstrap/bootstrap_classical_texts_jaimini.ts` | same, `.js` spellings | same |
| `bootstrap/bootstrap_classical_texts_kp.ts` | same | same |
| `bootstrap/bootstrap_classical_texts_tajaka.ts` | same | same |
| `aiops/probe_health_cron.ts` | `../../src/lib/aiops/health/bulk` | `platform/src/lib/aiops/` **does not exist** (the 95 `aiops` matches in the repo are all `00_ARCHITECTURE/aiops/*.md`) |
| `sla_probe_temporal.ts` | `../src/lib/retrieve/temporal` | `platform/src/lib/retrieve/` exists but has no `temporal`; and from `platform/scripts/` the `../src` hop lands outside `platform/` anyway |
| `sla_probe_planner_blind_tools.ts` | six `../src/lib/retrieve/*` | none exists |
| `retrieval/embedding_freshness_check.ts` | `../src/lib/storage` | resolves to `platform/scripts/src/lib/storage`; the real module is `platform/src/lib/storage/index.ts` — the specifier is one `../` short |
| `retrieval/test_classify.ts` | `../../src/lib/router/prompt.js` | `platform/src/lib/router/` has `errors.ts`, `retrieval_capability_spec.ts`, `types.ts` — no `prompt` |

Two more carry a **type-only** import of a missing module — `audit/replay.ts:37` and
`audit/smoke.ts:33`, both `import type { PredictionRow } from '../../src/lib/prediction/types'`
where `platform/src/lib/prediction/` does not exist. Type imports are erased, so those two still
run; they are tier 1 on their own merits and the stale type import is a separate defect.

Two further scripts have the same disease in **dynamic** form, which is why they are tier 1 and
not tier 3: `aiops/cutover_smoke.ts` (`await import('../../src/lib/aiops/probe/runner')` inside
`main()`) and `nim_one_shot_planner.ts` (`await import('@/lib/pipeline/manifest_planner')`). The
module body and `main()` **do** run; the dynamic import throws; the top-level `.catch` calls
`process.exit(1)` — T60's exact BEFORE-3 cell, reached by a different road.

**Why nothing has said so:** `platform/tsconfig.json` ends
`"exclude": ["node_modules", "scripts"]`. **The entire `platform/scripts` tree is outside the
TypeScript project.** M0-T60 reported `npx tsc --noEmit -p tsconfig.json` → 0 errors repo-wide,
and that is consistent: `tsc` never looked at any of these files. This also bounds what the
`fact-category-pin-lint`-style guards can be expected to see here.

I am reporting this and not fixing it — it is outside M0-T64's scope, which is a measurement.

---

## 7 — THE FINDING FOR ADHIKĀRIN (D-67 part 2's own stop condition)

> *"IF THE TRIAGE FINDS TIER 1 IS LARGE, THAT IS A FINDING TO BRING ADHIKĀRIN, NOT A REASON TO
> WIDEN THE GRANT UNASKED."*

**Tier 1 is 58 of 76 — 76% of the population, and 67 of 76 if the nine dead scripts are ever
revived.** I stopped. Nothing was repaired. What I would put to ADHIKĀRIN, as observation:

1. **"Repair tier 1 only" was scoped on an expectation that tier 1 would be a minority.** It is
   the overwhelming majority, because `process.exit` in a top-level `.catch` is the house style
   of this whole population — 53 of 76 files have it, and it alone accounts for 9 tier-1 files
   that are otherwise completely inert. The tier boundary is doing less separating work than the
   ruling assumed.
2. **A useful sub-split exists inside tier 1 and it is already measured**, if a smaller first
   dispatch is wanted: **44** are (a)+(c) — they open or acquire *and* kill the importer, T60's
   exact defect; **5** are (a) alone; **9** are (c) alone and are otherwise pure readers. The 5
   named in §5 are the ones where an incidental import reaches production secrets or deletes
   rows.
3. **D-67's "never copied from a sibling" rule makes 58 repairs 58 decisions, not one.** The
   population already contains **four different guard idioms** (`isDirectEntrypoint`,
   `IMPORT_ONLY`, an argv-regex `.test()`, an `isMain`/`endsWith` boolean) across the ten guarded
   files. Choosing per module is right; it is also why this is not one task.
4. **The ratchet in D-67 part 4 does not depend on the repairs happening first.** The itemised
   allowlist is generated and in `M0-T64-triage.json` (`ratchet_allowlist.files`, count 76) —
   a CI guard could be built against it now, on today's honest number, and shrink as repairs
   land. That is the D-54 disclosure shape the ruling itself points at.
5. **The allowlist count is 76, not 81**, so whoever builds the guard must use §2's command and
   this file's generated list, not the number in D-67.

Routed to `mailbox/to_conductor/`.

---

## 8 — What I did NOT do, and what I am unsure about

### 8.1 — Did not

- **Did not edit, repair, reformat or "quickly fix" any of the 76.** `git status` shows no
  modification under `platform/`; the only files I wrote are this report and its JSON.
- **Did not execute any script in the population**, in any form, in any environment. No sandbox
  run, no import, no `--help`. Everything above is static reading. The only commands I ran were
  `git ls-files`, `git grep`, `git status`, `ls`, `sed`, `awk`, `grep`, and Python that only
  read files.
- **Did not touch** `platform/scripts/audit/A3_env_matrix.md`, any `.env*`, any credential, any
  migration, any asset data, any registry row (P4, I13, I14 untouched).
- **Did not build the D-67 part 4 CI ratchet guard** — that is F-2/F-5's dispatch, not this one.
  I generated the allowlist it needs.
- **Did not fix the nine broken imports** (§6), the two stale type imports, or the
  `tsconfig` exclusion.
- **Did not verify that any script in the population works.** Nothing here is evidence that any
  of these 76 does its job. This is about what an *import* does.

### 8.2 — Unsure

1. **The 84/81 discrepancy is unexplained, not resolved.** I can defend 76 and 86 with commands
   whose output is above. I cannot reconstruct 84. If ADHIKĀRIN's scan is the correct one, five
   files are missing from my list, and a ratchet allowlist that is five short would let five
   files through. **This is the single most consequential open item in the report** and it should
   be settled by comparing lists, not counts, before the guard is built.
2. **The "dead on load" conclusion rests on ESM link semantics, which I reasoned about rather
   than tested** — deliberately, because testing it means importing the file, which is the
   hazard. If `tsx` resolves any of those nine specifiers by some route I did not model, the file
   is tier 1, not tier 3. I recorded `tier_if_import_resolved: 1` for all nine so the safe
   reading is available without re-deriving.
3. **(a) for the seven MCP gates is environment-conditional**, and I made a judgement call
   grading them YES. Someone could reasonably grade them TIER 3-in-PLAN-mode / TIER 1-in-LIVE.
   The flag is in the JSON either way.
4. **My detectors are regex over comment-stripped source, and regexes miss things.** I found and
   fixed one bug in my own scanner mid-run — a multi-line `import { a,\n b } from '…'` was not
   being matched, which silently emptied several import graphs (it is why
   `load_harvest_to_ledger.ts` first looked like a 1-module graph with no DB reach when it in
   fact calls `upsertConcepts`). I re-ran everything after the fix. I cannot promise there is not
   a second such bug; what I can say is that every non-obvious classification was confirmed by
   reading `main()`, not by trusting a detector.
5. **"UNDETERMINED = 0" is a strong claim and I want it read narrowly.** It means: for every one
   of the 76 I reached a determination I am willing to show evidence for. It does not mean the
   determinations are certain. The weakest are the five registry-catalogue generators
   (§3) — graded (a) NO because `getCatalog()` is an in-memory read and no dependency has a
   module-scope effect, but each loads ~200 modules and I did not read all 200.
6. **`_archived/seed-abhisek.ts` may not belong in the population at all** — if `_archived/` is
   meant to be dead, the right disposition is deletion, not a guard. That is a call for
   ADHIKĀRIN, not for me.
