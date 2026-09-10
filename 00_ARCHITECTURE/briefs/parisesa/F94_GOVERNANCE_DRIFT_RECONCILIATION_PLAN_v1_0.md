---
canonical_id: F94_GOVERNANCE_DRIFT_RECONCILIATION_PLAN
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-94
authored: 2026-08-21
authored_by: PARIŚEṢA-V4 repair lane (GA-2 authority — planning only)
execution_status: PARTIAL — the two detector-side repairs in §6 are EXECUTED; every
  registry/canonical-artifact mutation in §7 is NOT EXECUTED and requires a dedicated
  independent review before any session touches it.
measured_against: origin/main @ cfef54a25 ("fix(parisesa): F-62 — moolatrikona dignity tier never emitted (#1416)")
---

# F-94 — bounded governance-drift reconciliation plan

## §1 — What this document is, and what it is not

F-94 is booked as `kind=DEFECT, CL-22 governance/registry drift`, with the corpus's own
`current_evidence_class` = `CURRENT_GOVERNANCE_RESIDUAL_BASELINE_REPRODUCED`. Its next
executable action reads: *"Author and independently review a bounded governance registry
reconciliation plan … before any registry/canonical-artifact mutation."*

This is that plan. It is deliberately **bounded**, and it deliberately does **not**
attempt a 215-finding cleanup. Its claim is narrower and, I think, more useful:

> **161 of the 215 findings (74.9%) are one root cause, and that root cause is a
> false positive — a live registry being diffed against a document that was formally
> retired on 2026-04-27 and is required by hygiene policy never to be edited again.**

Two further root causes account for 52 more. Only **three findings in the entire report
are individually distinct**, and **two of those three turn out to be more than cosmetic**
— they are cases of a governance signal that cannot report what it claims to report
(CLAUDE.md §N.8). Those are escalated in §8 with their own candidate finding IDs rather
than folded into this bulk plan.

**No registry, canonical artifact, or manifest row was mutated by the lane that authored
this document.** The two repairs recorded in §6 are changes to the *detector* and to the
*CI ratchet* — never to the corpus the detector inspects.

---

## §2 — Reproduction and measurement method

Run against a clean clone of `origin/main` @ `cfef54a25`:

```
python3 platform/scripts/governance/drift_detector.py --repo-root . --session-id F94-RECON-2026-08-21
→ drift_detector: 215 findings; exit=3
```

Confirms the ledger's recorded baseline (216 findings, all MEDIUM/LOW, exit=3) within
one finding. The 1-finding delta is environmental, not corpus drift: `psql` is present on
this workstation and absent on the CI runner, which swaps one
`a3_schema_db_unreachable` (LOW) for one `schema_db_unreachable` (LOW). Despite the very
large number of PRs merged into `main` this session, the drift picture is **unchanged**
— which is itself evidence for the §3 diagnosis, since a report dominated by genuine
per-PR drift would have moved.

Severity distribution at baseline: **0 CRITICAL, 0 HIGH, 214 MEDIUM, 1 LOW.**

⚠️ **The `--repo-root .` in that command line is load-bearing, and that is a bug.** See
RC-3 (§4.3) — the same tree, walked with the default absolute repo-root, reported **825
findings / exit=2, including 571 spurious HIGH**. Any prior reproduction of F-94 that
used the relative form and any that used the default form were measuring different
things. This is repaired in §6.

---

## §3 — Root-cause taxonomy

| ID | Root cause | Findings | % of 215 | Disposition |
|---|---|---|---|---|
| **RC-1** | Live manifest diffed against `FILE_REGISTRY_v1_14.md`, SUPERSEDED 2026-04-27 | **161** | 74.9% | **False positive by construction** — §7, dedicated review |
| **RC-2** | §H.3.7 live-pointer scan run over `PHASE_B_PLAN_v1_0.md`, status SUPERSEDED | **51** | 23.7% | **Acceptable-and-intentional** — detector scope fixed, §6 |
| **RC-3** | `skip_dirs` matched against *absolute* path components | 0 here / 610 elsewhere | — | **Real defect, fixed** §6; escalated §8 |
| **RC-4** | `GOVERNANCE_STACK_v1_0.md` §1 does not name `MSR_v5_0.md` | 1 | 0.5% | **Genuine drift**, but a registry mutation — §7 |
| **RC-5** | `CHART_FACTS_SCHEMA.json` has no `columns` key, so the HIGH-severity column check is unreachable | 1 | 0.5% | **More than cosmetic** — escalated §8 |
| **RC-6** | DB unreachable from a non-prod network | 1 | 0.5% | **Acceptable** — honest degradation, §5 |

161 + 51 + 1 + 1 + 1 = 215. Every finding is accounted for.

---

## §4 — Class-by-class analysis

### §4.1 — RC-1 (161 findings): a live registry diffed against a retired one

Two checks produce these:

- `check_file_registry_agreement` (§H.3.5) → 84 × `registry_disagreement`
- `check_unreferenced_canonical` (§H.3.8) → 77 × `canonical_unreferenced`

The 77 `canonical_unreferenced` `canonical_id`s are a **strict subset** of the 84
`registry_disagreement` ids (`|A∩B| = 77`, `|B−A| = 0`). The 7 ids that appear only in
the H.3.5 set — `CDLM`, `CGM`, `L2_BODHA_CAMPAIGN_HANDOFF`, `LEL`, `MSR`, `RM`, `UCN` —
are the ones CLAUDE.md §D names directly, so H.3.8's second surface catches them and
H.3.5's does not. This is not 161 problems. It is one problem, counted twice, on 84
artifacts.

**Why it is a false positive.** Both checks read the *live* artifact set (in manifest
mode, all 128 `CAPABILITY_MANIFEST.json` entries) and require each basename to appear in
`00_ARCHITECTURE/FILE_REGISTRY_v1_14.md`. That file's own frontmatter reads:

```
status: "SUPERSEDED (2026-04-27 — content absorbed into CAPABILITY_MANIFEST.json;
         retained in place for historical audit and provenance)"
```

CLAUDE.md §C item 2 says the same thing from the other side: `CAPABILITY_MANIFEST.json`
is the "**new single source of truth** … Replaces the dual `FILE_REGISTRY` +
`CANONICAL_ARTIFACTS` registries," with `*_USE_MANIFEST=true` as the tooling default.

So the detector was cut over to the manifest for its **source** of canonical entries and
was never cut over for its **comparison surface**. It now asks a 2026-04-27 snapshot
whether it contains artifacts registered after 2026-04-27. It cannot. 84 of 128 manifest
entries (66%) fail; 44 pass only because they happen to predate the cutover.

Worse, this is **monotonically growing**: every correctly-registered new canonical
artifact adds exactly 2 findings forever. A "baseline" made of RC-1 is a baseline that
rises on good behaviour.

Worst, the emitted remediation is **actively harmful**. It reads *"Add a row for X in
FILE_REGISTRY"* — instructing a session to edit a document whose own frontmatter says
retained-in-place for historical audit, in direct violation of
`ONGOING_HYGIENE_POLICIES_v1_0.md` §A (archival retain-in-place). A detector that tells
sessions to violate hygiene policy is worse than a silent one.

**Sub-defect RC-1a.** `check_file_registry_agreement`'s docstring says it checks
"agreement on **CURRENT** rows," but the loop iterates `ca.artifacts.items()` with no
status filter. 11 of the 84 flagged entries are `status: PREDECESSOR`
(`REPORT_CAREER_DHARMA_v1_0`, `CLUSTER_ATLAS_v1_0`, `PATTERN_REGISTER_v1_0`, …) — rows
that are *supposed* to be absent from a CURRENT registry. The check does not do what its
own docstring says it does. Escalated in §8.

**Disposition: NOT fixed in this pass.** The correct repair — repoint or retire both
checks — changes what governance CI enforces about registry agreement, which is exactly
the class of change F-94's own framing gates behind independent review. Proposed shape in
§7.1.

### §4.2 — RC-2 (51 findings): live-pointer scan over a superseded plan

All 51 `phantom_reference` findings come from **one file**,
`00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md`, and all 51 already carry `whitelist_ticket:
WARN.2`. Every pointer is to a `python-sidecar/rag/*` or validator file deleted in the
WS-0C legacy purge — `p1_layer_separation.py`, `rag/embed.py`, `rag/graph.py`, and so on.

**Why these are acceptable-and-intentional, not drift.** `PHASE_B_PLAN_v1_0.md` has
`status: SUPERSEDED` in its frontmatter and is listed in CLAUDE.md §C item 5 among the
plans that are "SUPERSEDED-AS-COMPLETE" (M2, closed 2026-05-01). Its pointers are an
accurate description of the M2-era tree it documents. They are not stale *claims*; they
are correct *history*. Repointing them would falsify an archived record.

Three converging arguments that the defect is on the detector's side:

1. **The surfaces list already says so.** The comment directly above
   `GOVERNANCE_SURFACES_GLOBS` reads: *"Governance surfaces scanned for phantom
   references. **Excludes closed/time-stamped artifacts** per protocol §H.3.7."* Three
   entries in the list violate that stated rule — `PHASE_B_PLAN_v1_0.md` (SUPERSEDED),
   `FILE_REGISTRY_v1_14.md` (SUPERSEDED), `STEP_LEDGER_v1_0.md` (GOVERNANCE_CLOSED per
   CLAUDE.md §C item 8). The list has drifted from its own declared policy.
2. **§H.3.7 is by name a *live*-pointer scan.** A superseded plan has no live pointers.
3. **The booked remediation cannot occur.** WARN.2 books these for "PHASE_B_PLAN v1.0.3
   amendment cycle." There will be no v1.0.3 amendment cycle for a plan superseded three
   months ago. A ticket booked against an impossible event is not deferral, it is a
   permanent excuse.

**Disposition: FIXED in this pass** (§6.2). Only the §H.3.7 scan is scoped off the file;
`check_mp_pbp_alignment` (§H.3.3) still reads it, so MACRO_PLAN↔PHASE_B_PLAN alignment
coverage is unchanged. `FILE_REGISTRY_v1_14.md` and `STEP_LEDGER_v1_0.md` currently
produce **zero** phantom findings, so removing them would be a no-op today with a silent
future behaviour change — deliberately left for §7.3 rather than bundled in.

### §4.3 — RC-3: the detector's verdict depended on where the repo was checked out

Not visible in the 215 at all, which is precisely why it is dangerous.

`_build_basename_cache` walked the repo and skipped any file whose `p.parts` contained a
`skip_dirs` member. When `repo_root` is absolute — the **default**, `pathlib.Path.cwd()`,
and the form **CI itself uses** (`.github/workflows/ci.yml` runs the script with no
`--repo-root`) — `p.parts` includes every component of the checkout's own filesystem
location. A checkout under any directory named `.claude`, `venv`, `node_modules`,
`.next`, `.turbo`, or `__pycache__` matched every walked file, emptied the basename
cache, and turned every backticked pointer in every surface into a phantom.

Measured on the identical tree, no corpus change between runs:

| Invocation | Findings | Exit |
|---|---|---|
| `--repo-root .` (relative) | 215 | 3 |
| default (absolute cwd, under a `.claude/…` path) | **825** | **2** (571 spurious HIGH) |

Exit 2 is a CI-failing code under the gate's own policy (`0` or `3` only). A governance
gate whose verdict depends on the checkout's parent directory name is not measuring what
it claims to measure — CLAUDE.md §N.8, the Earned-Signal Principle, applied to the
detector itself.

**Disposition: FIXED in this pass** (§6.1) and **escalated with its own finding ID**
(§8.1), because "the detector's own result is environment-dependent" is a class of
problem worth tracking separately from "the corpus has stale pointers."

### §4.4 — RC-4 (1 finding): `GOVERNANCE_STACK` missing `MSR_v5_0.md`

`00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md` §1's version registry does not name
`MSR_v5_0.md`, the CURRENT MSR per CLAUDE.md §D.

Unlike RC-1, this one is **genuinely real**. `GOVERNANCE_STACK_v1_0.md` carries
`status: CURRENT (updated in-place; next version will be v2.0)` — it is a live registry,
not a retired one, so a CURRENT canonical artifact missing from it is exactly the GA.1
registry-disagreement failure mode CLAUDE.md §I B.8 names.

**Disposition: NOT fixed in this pass.** It is a one-row edit, but it is a *registry*
edit, and F-94's framing gates registry mutation behind a dedicated review. Queued at
§7.2. Being small is not the same as being pre-approved.

### §4.5 — RC-5 (1 finding): the chart_facts column check has never been able to run

`check_chart_facts_schema` is documented as "B-10 — CHART_FACTS_SCHEMA.json column
presence verification," and its HIGH-severity arm emits `chart_facts_column_missing` for
any declared column absent from the live table, plus an explicit check that the B-series
columns (`ayanamsha_id`, `engine_version`, `computed_at_iso`, `chart_id`, `fact_id`) are
present.

It reads `schema.get("columns", [])`. The actual 192 KB
`platform/scripts/governance/CHART_FACTS_SCHEMA.json` has exactly three top-level keys —
`schema_version`, `categories` (147), `channels` (4) — and the string `"columns"` appears
**zero** times in the file. It is a fact-category/allowed-key taxonomy, a different
artifact from the column contract the check expects, and `git log` shows no revision in
which it held a `columns` array.

So `declared_columns` is always empty, the function always returns early on the MEDIUM
`schema_file_empty`, and **the entire HIGH-severity live-column verification arm is
structurally unreachable and always has been**.

This is the §N.8 defect class verbatim: *"what specifically does this signal claim, and
what code path would have to run — and fail — for the signal to correctly read false?"*
For `chart_facts_column_missing`, no such path exists. The one MEDIUM finding in the
report is not a small problem; it is the visible tip of a HIGH-severity check that has
never executed.

**Disposition: NOT fixed in this pass** — the repair requires deciding what the true
column contract is and verifying it against a live DB, which is its own effort with its
own review. **Escalated with its own finding ID** (§8.2).

### §4.6 — RC-6 (1 finding, LOW): DB unreachable

`a3_schema_db_unreachable` — `psql` cannot authenticate to `127.0.0.1:5433` from a
workstation with no production credentials.

**Acceptable and correct as-is.** The check degrades honestly: it reports LOW with the
literal connection error as evidence, rather than reporting a clean pass it could not
have earned. That is §N.7 item 6 (an honest null beats an invented judgment) working as
designed. **No action.** It should not be whitelisted away either — a LOW that says "I
could not check" is the correct output and should stay visible.

---

## §5 — Scope boundary of this plan

This plan does **not** propose a 215-finding cleanup, and recommends against attempting
one. The bounded claim:

- **RC-2 + RC-3 are the highest-leverage low-risk subset** — two localized changes to the
  detector, no corpus surface touched, closing 51 findings and one environment-dependence
  defect. **Executed in this pass** (§6).
- **RC-1 is the highest-leverage change overall (161 findings, 74.9%) and must not be
  done here.** It is registry-semantics work: deciding whether §H.3.5/§H.3.8 are
  repointed at the manifest, restricted to pre-cutover artifacts, or retired as
  superseded checks. Specified but **not executed** (§7.1).
- **RC-4 is real and one row wide, and still must not be done here** — it is a registry
  mutation (§7.2).
- **RC-5 needs its own effort and its own review** (§8.2).
- **RC-6 needs nothing.**

---

## §6 — Executed in this pass (detector-side only)

Branch `parisesa/repair-F94-governance-drift`. Two source changes plus one CI ratchet.
**Zero** governance markdown, registry row, manifest entry, or canonical artifact was
modified.

### §6.1 — RC-3 repair: match `skip_dirs` against the repo-relative path

`platform/scripts/governance/drift_detector.py`, `_build_basename_cache` — the walk now
computes `p.relative_to(repo_root).parts` before testing `skip_dirs`, so the checkout's
own filesystem location can no longer poison the cache.

Measured, same tree, default (absolute) repo-root, before → after:

```
825 findings; exit=2   →   215 findings; exit=3
```

The absolute-root and relative-root invocations now agree exactly (215 = 215). No change
whatever on a clean checkout path, which is why this is safe to land ahead of review: it
can only remove environment-dependent false HIGHs, never suppress a real finding.

### §6.2 — RC-2 repair: scope the live-pointer scan off a superseded plan

`GOVERNANCE_SURFACES_GLOBS` no longer lists `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md`, per
the argument in §4.2 and per the list's own stated exclusion rule. `check_mp_pbp_alignment`
(§H.3.3) still reads the file. `WARN.2` is **retained** in `WHITELIST_TICKETS` as audit
trail and is now expected to match nothing; deleting it is queued at §7.3 rather than
done silently here.

Measured, before → after:

```
215 findings; exit=3   →   164 findings; exit=3   (−51, all RC-2)
```

### §6.3 — Ratchet the CI baseline down

`.github/workflows/ci.yml`: `DRIFT_BASELINE_MAX` **216 → 165**. The gate's own comment
invites this — *"Lowering a ceiling after cleanup is encouraged; raising one requires a
recorded ruling, not a quiet edit."* Leaving the ceiling at 216 after a 51-finding
reduction would hand the cleanup straight back as 51 units of slack in which new drift
could accumulate unseen. The `+1` over the measured 164 preserves the same one-finding
runner-vs-workstation `psql` allowance the 216 figure carried over 215.

### §6.4 — Verification

- `python3 -m pytest platform/scripts/governance/__tests__/` → **17 passed**
  (`test_drift_detector_a3.py`, `test_d08_pointer_integrity.py`).
- `.github/workflows/ci.yml` parses as valid YAML.
- Post-change detector: **164 findings, exit=3**, severity distribution 163 MEDIUM /
  1 LOW, 0 HIGH, 0 CRITICAL — under the new 165 ceiling.

---

## §7 — Queued: requires a dedicated independent review (NOT executed)

Each item below is specified so a reviewed execution session can act without re-deriving
the analysis. **None of it is authorized by this document.**

### §7.1 — RC-1 (161 findings): repoint or retire §H.3.5 and §H.3.8

The decision to be reviewed is *which* of three, not whether to edit FILE_REGISTRY
(option (d) below is ruled out on hygiene grounds):

- **(a) Repoint.** §H.3.5 becomes manifest↔`CANONICAL_ARTIFACTS_v1_0.md` parity;
  §H.3.8's second surface becomes `CAPABILITY_MANIFEST.json`. Preserves the GA.1 intent
  ("registries must not disagree") against the surfaces that are actually live.
- **(b) Retire with an honest marker.** Both checks emit exactly **one** MEDIUM finding
  stating that their comparison surface was superseded on 2026-04-27 and the check is
  inapplicable in manifest mode — never 161 findings each instructing an archival edit.
  Weaker than (a), but honest, and strictly better than the status quo.
- **(c) Freeze the comparison set.** Restrict both checks to artifacts registered on or
  before 2026-04-27, so the pre-cutover parity guarantee is still enforced and the count
  stops growing on good behaviour.
- **(d) Backfill FILE_REGISTRY. RULED OUT** — violates `ONGOING_HYGIENE_POLICIES` §A.
  Recorded here only so a later session does not rediscover it as an option.

Whichever is chosen, **RC-1a must be fixed in the same change**: filter by status so the
check matches its docstring and stops flagging 11 PREDECESSOR rows.

Expected effect: −161 findings (164 → ~3). Ratchet `DRIFT_BASELINE_MAX` to match.

### §7.2 — RC-4: add `MSR_v5_0.md` to `GOVERNANCE_STACK_v1_0.md` §1

One row. Real drift. A registry mutation, therefore gated. The reviewing session should
confirm at the same time whether `GOVERNANCE_STACK_v1_0.md` is still the intended live
surface post-manifest-cutover, or whether §H.3.6 belongs in the §7.1 decision alongside
§H.3.5/§H.3.8 — the three checks may share one answer.

### §7.3 — Residual tidy-ups (low value, non-urgent, bundle with §7.1)

- Remove `FILE_REGISTRY_v1_14.md` (SUPERSEDED) and `STEP_LEDGER_v1_0.md`
  (GOVERNANCE_CLOSED) from `GOVERNANCE_SURFACES_GLOBS`, aligning the list with its own
  stated exclusion rule. Zero findings today; do it as a deliberate reviewed change, not
  as a silent side effect.
- Retire the now-dead `WARN.2` ticket, and `WARN.5` (books
  `B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE.md`, which is not in the surfaces list at all, so it
  can never fire).
- `PHASE_B_PLAN_v1_0.md` frontmatter says `version: 1.0` while its body header says
  `Version: 1.0.3` and its changelog records a `v1.0.4` amendment. Internal version
  disagreement inside an archived document; note it, do not rewrite the archive.

---

## §8 — Escalated: individual finding IDs, not part of this bulk plan

Per F-94's framing, drift that could cause real behavioural error gets its own ID rather
than being absorbed here. IDs below are **candidates** for the ledger owner to assign.

### §8.1 — `F-94.a` — drift_detector's verdict was checkout-path-dependent (**FIXED**, needs its own ledger row)

**Severity: behavioural, not cosmetic.** A governance gate returned 215/exit=3 or
825/exit=2 for the *same tree* depending only on the checkout's parent directory name
(RC-3, §4.3). Consequences worth tracking independently of the fix: any historical F-94
reproduction is ambiguous unless its invocation form is known; a CI runner or agent
sandbox whose workspace path contains `venv`, `node_modules`, `.claude`, `.next`,
`.turbo`, or `__pycache__` would have failed the gate with 571 fabricated HIGH findings
and no corpus defect; and conversely the relative-root form was the only one anyone had
verified. Repaired in §6.1. Recommend a regression test asserting that the detector
returns an identical finding count for relative and absolute `--repo-root` on the same
tree — the fix is one line and one line is exactly what a future refactor drops.

### §8.2 — `F-94.b` — the chart_facts column-verification arm is unreachable (**NOT fixed**)

**Severity: §N.8 Earned-Signal violation, HIGH-severity arm affected.**
`check_chart_facts_schema`'s `chart_facts_column_missing` (HIGH) — including the explicit
B-series check for `ayanamsha_id`, `engine_version`, `computed_at_iso`, `chart_id`,
`fact_id` — has never been able to execute, because the schema file it reads has never
had the `columns` key it looks for (RC-5, §4.5). A B-series column could be dropped from
live `chart_facts` today and this check would report the same single MEDIUM it has always
reported. Fixing it means establishing the real column contract and verifying it against
a live DB: its own effort, its own review, its own finding.

### §8.3 — `F-94.c` — §H.3.5 does not check what its docstring says (**NOT fixed**)

**Severity: cosmetic today, correctness-relevant once §7.1 lands.** The docstring says
"agreement on CURRENT rows"; the loop filters by nothing, flagging 11 PREDECESSOR
entries. Low harm while the whole check is a false-positive generator; it becomes a real
correctness bug the moment §7.1 repoints the check at a live surface. Must be fixed
inside the §7.1 change, not after it.

---

## §9 — Recommended sequencing

1. **Now (this PR, §6):** RC-3 + RC-2 + ratchet. 215 → 164, exit=3, no corpus surface
   touched. Independently reviewable in a few minutes.
2. **Next, gated on a dedicated review:** §7.1 (RC-1 + RC-1a/F-94.c) — the 161-finding
   decision. This is the one that actually closes F-94.
3. **With or after (2):** §7.2 (RC-4) and §7.3 residuals, plausibly one reviewed session.
4. **Separately tracked:** F-94.b (§8.2), which is not governance-registry work at all
   and should not wait on, or block, any of the above.

F-94 itself should stay open until step 2 lands. This pass moves it from
`CURRENT_GOVERNANCE_RESIDUAL_BASELINE_REPRODUCED` to *baseline diagnosed, 24% closed,
75% specified-and-gated* — which is progress, but is not closure, and this document does
not claim otherwise.
