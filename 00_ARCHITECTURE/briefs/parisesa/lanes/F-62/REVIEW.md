---
lane: F-62
stream: S6_ADHARA
stage: R (REVIEW) — Stage R second pass, PASS 2
reviewer: VERIFIER (author != reviewer — DIAGNOSIS.md/SPEC.md authored by ADHARA-LEAD)
reviewed_artifact: SPEC.md (as of commit 4a9264b51) against PR #1296 head 7843cf3df03f2ded96dfe79761b21d4e5b09f669 (PASS 1); re-reviewed against SPEC.md revision + PR head 78bfd64d1d5e3ce298a59b215424e4be71d533db (PASS 2)
verdict: COMPLETE (PASS 2, superseding PASS 1's INCOMPLETE-RETURN below — kept for audit trail, not deleted)
---

# F-62 — REVIEW (Stage R)

## PASS 2 — COMPLETE (re-verification, new head 78bfd64d1)

The conductor reported all three PASS-1 deficiencies addressed and asked for re-verification
"before completing your current task," explicitly noting to "take whatever time you need to
actually re-derive rather than trust the summary." Did exactly that — nothing below is taken
from the conductor's characterization.

**Method.** Fetched `origin/par/coordination` (picked up the revised SPEC.md/DIAGNOSIS.md,
253 lines changed) and `origin/ekv/b-01-dignity-oracle` (new head). Confirmed via
`gh pr view 1296 --json headRefOid` that the live PR head is genuinely `78bfd64d1...`, matching
the report. Checked out that exact commit in a fresh scratch worktree (not trusted from a
branch name) and re-ran everything from scratch.

**Deficiency 1 (stale SPEC.md/DIAGNOSIS.md) — CLOSED.** Read the revised SPEC.md §2 file list
(now 9 files, matching `gh pr view 1296 --json files` exactly, including
`l0_dignity_reference.py` and `bg_dignity_reference.py` which PASS 1 found missing) and §5's
corrected "Extraction status" section (no longer says "deliberately not done"). Read
DIAGNOSIS.md §3's updated note — accurately describes the extraction, and independently
re-confirmed the identity claim it makes (`bg_dignity_reference._DIGNITY_REFERENCE is
l0_dignity_reference.DIGNITY_REFERENCE`) via the same test file, unchanged since PASS 1.

**Deficiency 2 (`l1_strength.py:65` exclusion reason) — CLOSED.** SPEC.md §4 and DIAGNOSIS.md
§4 item 2 now both state the real reason (lease granted post-Phase-0, deferred instead for a
genuine open classical-semantics question about Sthana Bala's own MT treatment) and explicitly
mark it a tracked follow-up rather than a dropped thread. This is the honest resolution PAR-R-7/
SP-8 point toward — not rushing a guessed answer to a classically uncertain question just to
close a checkbox — and it correctly separates "lease question: resolved" from "classical
question: still open," which the original text conflated.

**Deficiency 3 (D-01b allowlist regression) — CLOSED, and closed better than the minimum fix.**
Read commit `78bfd64d1`'s diff to `no_local_dignity_table_allowlist.json`: the
`ga_vargas_writer.py` entry is repinned from an exact line number to a content `pattern` match
on the dict's opening `"Sun": {...}` entry — immune to the whole class of future line-drift, not
just this one instance (this was my own review's "recommended" option, not just the minimum
"bump the number" fix). The stale `ga_structural_writer.py:4852` entry is removed; independently
confirmed (not assumed) that file now produces zero scanner hits at all
(`scan_python_file` returns `[]`), so removing the entry didn't silently un-cover a live
violation. Ran `check_no_local_dignity_table.py --json` myself on the new head:
`{"total": 2, "allowlisted": 2, "new": [], "pass": true}`, exit 0. Ran `--self-test`: PASS.
Cross-checked against **live GitHub CI** on the actual PR (not just my local run):
`D-01b — No Local Dignity Table (WARN)` is now `SUCCESS` on PR #1296's current head — matches.

**Exit test re-run at the new head:** `python3 -m pytest brahmagyan/__tests__/test_dignity_oracle.py -q`
→ `39 passed in 0.04s`, identical to PASS 1 (this commit only touched the allowlist JSON, no
test-code change, so no regression expected or found).

**Regression check, redone against the new head's live CI, not just PASS 1's snapshot.** Pulled
PR #1296's current `statusCheckRollup` and cross-referenced every non-required failing check
against `origin/main`'s own tip (`5ff46c2a0`) check-runs, this time with `--paginate` (PASS 1's
non-paginated pull happened to truncate before reaching one relevant entry — caught and closed
the gap this pass, not left as an unchecked assumption): `D-01a`, `D-01c`, `D-01d`,
`TAP-5/TAP-7/S-13`, `Boot-time pointer validation`, `D-08` are all confirmed pre-existing
`failure` on `main`'s own tip commit (both of its two workflow runs) — none are new. The five
required status checks per the branch ruleset (`gh api .../rulesets/20141220`) are
`TypeScript (src only)` SUCCESS, `TAP-6` SUCCESS, `Secret Scan` SUCCESS, `Unit Tests` and
`Governance Gates` both `IN_PROGRESS` (not failed) at time of this check —
`mergeStateStatus: BLOCKED` reflects those two still running, not a hard block.
`mergeable: MERGEABLE`.

**Verdict: COMPLETE.** All three named deficiencies genuinely closed, independently re-verified
end to end (docs read, code read, checker re-run, tests re-run, live CI cross-checked), not
re-derived from the conductor's summary. This is INTEGRATOR's first real merge candidate on my
side — recommend proceeding once the two in-progress required checks land green (I'd expect
them to, since neither touches anything this lane's diff reaches, but that's INTEGRATOR's own
confirmation to make at merge time, not mine to assume here).

---

## PASS 1 — INCOMPLETE-RETURN (kept for audit trail; superseded by PASS 2 above)

## Note on how this review was triggered

The conductor flagged F-62 as blocking and asked me to prioritize it, noting it "went
through PAR-R-1/2/3/6/7 rulings directly, an unusual path, worth naming explicitly in your
verdict" and to treat SPEC.md + the PR diff as the review pair since build preceded formal
sign-off. I'm naming it explicitly, as asked — but I did not take "PAR-R-1/2/3/6/7 exist and
say what the message claims" on the message's word. Per FM-09 I re-derived: fetched
`origin/par/pratinidhi-ledger` and read `LEDGER_PRATINIDHI.md` directly. PAR-R-1, 2, 3, 6, 7
are genuine, specific to F-62, and well-reasoned. I also independently re-ran the exit test on
both `origin/main` (red) and the PR's actual head sha (green), re-derived PR #1296's live
GitHub state (mergeable/CI/branch-protection rules) rather than trusting "39/39 passing,
mergeable" as reported, and read the actual diff at the PR's true head rather than SPEC.md's
description of it. That last check is where this lane's real gap sits: **the build-before-
review path did produce a genuine artifact-currency problem, not just an unusual paper trail**
— see deficiency 1.

## The seven questions

### 1. Does the spec address the mechanism or merely the symptom?

**Mechanism.** Root cause (SPEC.md §1) is stated at the right level: three independent local
dignity-classification call sites drifted because no shared, degree-aware classifier existed.
The fix is a real shared oracle (`brahmagyan/dignity_oracle.py`, `classify_dignity(graha,
sign_name, degree_in_sign)`), not a patch to any one call site. Independently confirmed by
reading the diff: all three original consumers (`ga_structural_writer.py:4874`,
`ga_vargas_writer.py:488`, `bo_pratijna_v4_engine.py:293`) call the same imported function.

### 2. Does every sub-claim from D-2 map to a spec element?

**Mostly, with one live gap.** SPEC.md §7's coverage table (C1→`ga_structural_writer.py`
wiring, C2→`ga_vargas_writer.py` `_compute_dignity` rewrite, C3→shared oracle + 3 consumers +
recurrence guard) is accurate against the diff I read. But DIAGNOSIS.md §4 found a **fourth**
consumer site, `brahmagyan/ganita/l1_strength.py:65` (`PLANET_DIGNITY`, Shadbala Sthana Bala),
and both DIAGNOSIS.md and SPEC.md give its exclusion reason as "out of S6's lease." That
reason is **no longer true**: `LEASES.json`'s `S6_ADHARA.owns` array now includes
`platform/python-sidecar/brahmagyan/ganita/l1_strength.py` with the note *"ADDED post-Phase-0,
4th dignity-oracle consumer site found during F-62 build, kept with the same team already
touching the other 3 sites."* The lease was granted; the code at `l1_strength.py:65` has not
been touched (confirmed: it's still the pre-existing allowlisted violation, unchanged). The
written exclusion reason and the live fact have diverged — this is exactly the sub-claim-
mapping gap Q2 exists to catch, one level removed (not "unmapped," but "mapped to a reason
that is now false").

### 3. Would the exit test genuinely fail today? (RUN it — TIER1 lane)

**Yes, confirmed both directions, independently run:**
- On `origin/main` (5ff46c2a0), `python3 -m pytest brahmagyan/__tests__/test_dignity_oracle.py -q`
  → collection error, `ModuleNotFoundError: No module named 'brahmagyan.dignity_oracle'`.
- On the PR's actual head (`7843cf3df03f2ded96dfe79761b21d4e5b09f669`, checked out in a scratch
  worktree, not trusted from a branch name), same command → **39 passed in 0.04s.** Matches the
  conductor's "39/39" figure — independently reproduced, not inherited.

### 4. Are all sibling sites from D-4 covered, or excluded with a stated reason?

**Partially — see deficiency 2.** `ga_vargas_writer.py::_build_saptavargaja_rows` (the second,
independently-discovered MT check) is genuinely fixed: read the diff at commit `933f680a0`,
confirmed it routes through `classify_dignity()` with a real `degree_in_sign`, and the
commit message itself correctly predicts and discloses that D-01b will still flag the file's
now-inert `DIGNITY_TABLE` dict (kept only for the "own" sign lookup, a documented, reasoned
decision). `l1_strength.py:65` is excluded, but per Q2 above, on a stale reason.

### 5. Is there a recurrence guard, and does it actually detect the defect class?

**Yes, genuinely.** Two real detectors, both read and reasoned about, not assumed:
- `test_data_matches_bg_dignity_reference_source_of_truth` — an `is` identity assertion
  (`_DIGNITY_REFERENCE is DIGNITY_REFERENCE`), not mere value-equality, so it fails if the
  writer ever reintroduces a local copy instead of importing the shared module.
- `test_l0_dignity_reference_matches_seeded_migration_250` — parses migration 250's actual SQL
  `VALUES` block and compares it field-by-field against `l0_dignity_reference.DIGNITY_REFERENCE`.
  This is the Python↔DB-seed seam PAR-R-6 named as the one thing extraction does *not* close;
  a real detector exists for it, per §N.8/SP-5.
- D-01b (`check_no_local_dignity_table.py`) itself is a third, CI-level guard against this
  defect class re-appearing anywhere in the tree — see deficiency 3 for why its allowlist
  needs a one-line correction as part of this lane, not a separate one.

### 6. Could this regress any of the 27 controls, or another stream's lane?

**Yes — a real, currently undisclosed regression, found by running the actual checker, not by
reading its CI log text.** See deficiency 3. Confirmed the PR's own diff is scoped to exactly
8 Python files (`gh pr view 1296 --json files`), none of which touch any other stream's lease,
so no cross-stream file collision. The regression is narrower and more specific: this PR's own
edit (adding an import line above `ga_vargas_writer.py`'s module-level `DIGNITY_TABLE`) shifts
that dict from line 134 to line 135; the D-01b allowlist entry is pinned to line 134
(exact-line match, not pattern match); so merging as-is flips D-01b from **PASS on
`origin/main` today** (confirmed: I pulled main's own check-runs and it is
`success — D-01b — No Local Dignity Table (WARN)`) to **FAIL** — for content that is byte-
identical pre-existing debt, not a new local table. WARN-only and not in the branch ruleset's
required-checks list (confirmed via `gh api .../rulesets/20141220` — the five required checks
are TypeScript/Unit Tests/Secret Scan/Governance Gates/TAP-6, D-01b is not among them), so this
does not block the GitHub merge — but it is an undisclosed governance-baseline flip from green
to red, exactly the class of thing this campaign polices in *other* lanes.

Separately confirmed as **not** a regression from this PR: `TAP-5/TAP-7/S-13`, `Boot-time
pointer validation (SC-17/18/19)`, `D-08 — Pointer Integrity Tests`, `D-01c`, `D-01d` are all
already failing on `origin/main`'s own tip commit (pulled `origin/main`'s check-runs directly)
— pre-existing red, unrelated to F-62's Python-only diff.

### 7. Is anything in the spec unverified assumption rather than read code?

**The spec's problem is not unverified assumptions — everything it does claim is read-code-
accurate. The problem is that it describes an earlier state of the branch than what's actually
on PR #1296 today.** SPEC.md §5 says *"Deliberately not done in this pass: full extraction of
the degree table into one dependency-free shared module... this is a follow-up lane, not a
blocker to landing this fix."* That was true when SPEC.md was last written (commit `4a9264b51`).
It is no longer true: the PR's actual head (`7843cf3df`) **does** carry the full extraction —
confirmed by reading `platform/python-sidecar/brahmagyan/l0_dignity_reference.py` (new,
stdlib-only, `import json` / `from typing import Any` only) and confirming both
`bg_dignity_reference.py:50` and `dignity_oracle.py:44` import `DIGNITY_REFERENCE` from it.
SPEC.md §2's file list is also short two files relative to the PR's actual diff
(`l0_dignity_reference.py` new, and `bg_dignity_reference.py` itself is never listed as
touched, though `gh pr view 1296 --json files` shows it in the changeset). This is a direct
consequence of the build-before-review path the conductor asked me to name: PAR-R-6/PAR-R-7
landed *after* SPEC.md was written, the code was updated to match, and the paper trail was not.

## Verdict: INCOMPLETE-RETURN

Not because the fix is wrong — it is genuinely good work, and I want that on the record
plainly: the oracle is well-designed (half-open MT interval matches PAR-R-2's ruling exactly,
including the boundary goldens PAR-R-2 mandated for every MT-bearing graha, which I found
present and passing — Sun/Moon/Mars/Mercury/Venus/Saturn/Jupiter all have boundary tests, plus
the two Moon/Mercury "currently unreachable" tests that honestly document HN-2's open question
rather than silently omitting it); the extraction is exactly what PAR-R-6 ordered and doesn't
touch the FROZEN contract (verified: `@register`, `run(ctx)`, `WriterBase` all present and
unmoved in `bg_dignity_reference.py`); the recurrence guards are real detectors, not green
flags with no failure path; and the red→green exit-test transition is genuine, independently
reproduced by me on both ends.

It's INCOMPLETE-RETURN because Stage S's own contract (§3: "Files to change... Sibling sites
covered... or a written reason a site is excluded") isn't satisfied by what's currently
written down, and one of the gaps (deficiency 3) is a real, if small, undisclosed regression —
exactly what Q6 exists to catch before merge, not after.

### Named deficiencies (all cheap; none require redesigning the fix)

1. **SPEC.md is stale relative to the PR's actual head.** Update §2's file list to include
   `brahmagyan/l0_dignity_reference.py` (new) and
   `pipeline/orchestrator/writers/bg_dignity_reference.py` (now imports the extracted module);
   update §5 to state the extraction was completed per PAR-R-6/PAR-R-7 rather than "deliberately
   not done." DIAGNOSIS.md's mechanism section (§3) should likewise note the single-source
   module now exists, replacing "a static reproduction of ... `_DIGNITY_REFERENCE`" (accurate
   pre-extraction, inaccurate now — post-extraction there is no reproduction, there is one
   shared import).
2. **The `l1_strength.py:65` exclusion reason needs correcting, not just re-flagging.**
   "Out of S6's lease" is false as of the post-Phase-0 lease grant. Replace with the real
   current reason — DIAGNOSIS.md §4 item 2 already has it half-written (*"does BPHS's Sthana
   Bala also want a degree-gated MT distinct from own-sign credit... not determined this
   session, needs its own diagnosis"*) — and either open that as an explicit tracked follow-up
   (not silently dropped now that lease routing is resolved) or fold it into this lane if the
   classical question turns out to be trivial.
3. **Fix the D-01b allowlist line-drift before merge.** One-line change:
   `no_local_dignity_table_allowlist.json`'s `ga_vargas_writer.py` entry, `"line": 134` →
   `"line": 135` (or switch to `pattern` matching on the dict's opening keys, which would be
   immune to this exact class of future drift — recommended, since the next import added above
   this dict will just move the problem to a new line number again). Without this, merging
   flips D-01b from PASS to FAIL on `main` for zero-new-content reasons, undisclosed in any
   lane document today.

### What does NOT need to happen

No new Stage B work on the substantive fix. No re-litigating PAR-R-1/2/3/6/7 — I independently
verified all five against source and they stand. No expansion of scope to fix `l1_strength.py`
itself in this PR (the classical-semantics question is genuinely open and rushing it would be
exactly the kind of thing PAR-R-7 warns against — shipping a decision framed as caution). The
three deficiencies above are a documentation sync + a one-line JSON edit; I'd expect this lane
back at COMPLETE within one short pass.

## Regression check against the 27 CL-00 controls

Not run as a separate battery this pass (S6's own ledger and this review's file-scope check
both confirm the diff touches only Python dignity-classification files, no CL-00-adjacent
surface) — will re-run the CL-00 cheap subset at Stage V per plan §3 once deficiencies above
are closed and the lane is re-submitted.
