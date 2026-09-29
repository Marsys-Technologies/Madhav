---
artifact: L3_KSHETRA_FINAL_BRIEF_PROMPT
version: "1.2"
status: READY — paste into a new conversation
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.2 (2026-09-29, review pass 2 / FI-8): the leftover line telling this session to emit a ruling as decided is removed (its own Corrections forbid it); the sealed brief is reported as review with evidence, and F1.K closes when Strategic Suvarṇa records the native's seal (SEAL-K); the evidence folder is an absolute path under /Users/Dev/suvarna/evidence; the tools run from the hq worktree; F-3 means the cascade removed from all eight keys."
  - "1.1 (2026-09-29, review pass 1 / FI-8): census command corrected (--out is a file; the read-only credential is sourced; runs through the census lock so only one census runs at a time); certification condition (D2); native rulings are recorded as decided only by Strategic Suvarṇa; record the tier-4 template revision the brief follows."
  - "1.0 (2026-09-29): first issue, on the native's instruction that each L3 focus family gets its own session to seal a final brief and implement it."
---

# L3 Kṣetra — seal the final brief, then implement it

**Session name:** L3 Kṣetra. You own the Kṣetra family end to end: a final brief the native seals, then its implementation. The Suvarṇa campaign will not change Kṣetra code; its L3 analysis will evaluate whatever you have produced most recently.

## 1 · Where things stand (verify every line before relying on it)

- **Asset:** `ka_kshetra` → `kala_field`, plus its window, salience, insight, timeline and snapshot tables.
  - Nine open Nikaṣa gaps; its `Idem.pattern` gate reads FAIL (the rebuild is refused).
  - Nirmāṇa never froze it.
- **The canonical chart `482012f1…` has never had a successful full build.**
  - It holds 8,570,075 rows (25 event classes) left over from 29 build attempts on 2026-09-10/11. The last one died with "the connection is lost".
  - Only 14 of the 25 classes got windows.
  - Nothing reached the salience, insight, timeline or snapshot stages, so nothing is published.
- **A wrong time axis.** Transit times counted from 2000 are placed on a birth-relative axis, a shift of about 15.9 years (measured live).
- **85.7% of windows** rest on a synthetic baseline rather than real event-rate data.
- **The only published field** is a 6-class run on `1c826d5a…` from 2026-08-12. It predates later fixes and has the same axis defect.
- **Rebuilds are refused by design.** Since PR #2607 the writer raises `KshetraReplacementHeld` on any populated chart until versioned publish-then-switch storage (W7) exists. W7 is not built.
- **Stage 3** (code fixes proven on fixtures) was authorized on 2026-09-24 and never started. No Kṣetra code has changed on `main` since #2607.
- **A Kṣetra writer change sits on the Gochara lane's branch**, not on `main`. Its migration 1084 is already applied in production, and it lands with PR #2731.
- **Other defects:**
  - the null test is scoped to the whole chart instead of per route;
  - the synthetic-baseline flag is computed, then dropped;
  - a forbidden read up into L4;
  - two tables that differ on every rebuild;
  - phantom dependencies (`bo_upaya`, `bo_sangati`, declared but never read) and about ten real reads left undeclared, including Gochara's windows;
  - nothing serves `kala_field` (`query_field_trajectory` does not exist), and L5's `mi_bhara` attaches to an arbitrary unpublished snapshot;
  - real priors exist for only 6 classes, with no fitted weights.
- **Upstream Gochara is changing.** It moves from `'3.0'` to a new full-century generation, and Kṣetra must be rebuilt on it. The L3 Gochara session publishes the interface (table, generation, authority filter, horizon).

**Read first:**
1. `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/l3_recon/KSHETRA_RECON.md` (the current state, with a source for every claim).
2. `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` §3 and §4.
3. The family's own documents, as cited in the reconciliation report: `KSHETRA_ELEVATION_BRIEF_v1_0.md`, `KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md`, `KSHETRA_RULING_SHEET_v1_0.md`, `KSHETRA_STAGE3_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md`, `KSHETRA_ABLATION_PREREGISTRATION_v1_0.md`, `KSHETRA_INBOUND_RECONCILIATION_v1_0.md`.

## 2 · Settle these first

Your brief brings each of these rulings to the native, with options, a recommendation and its consequence:

- **F-1 — the rebuild path.**
  - Option 1: build W7 first. The recommendation to test is to generalise Gochara's "build a candidate generation, then switch authority" pattern rather than build a second mechanism. Confirm or refute this with the L3 Gochara session.
  - Option 2: authorize an interim archive-and-clear of about 11 million rows (about 6.7 GB) with a verified snapshot.
- **F-4 — scope.** Stay at 6 classes (ruling 1 made the 6-class run the product), or reopen it.
- **The Saṅgam question (F-2) touches you.** ŚAḌ-DARŚANA would retire Saṅgam into `kala_field`. The L3 Saṅgam session will ask you; answer from Kṣetra's side before it recommends.

## 3 · The brief

Write `00_ARCHITECTURE/briefs/l3_families/KSHETRA_FINAL_BRIEF_v1_0.md`.

1. **Follow the asset elevation template:** `/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` (identity, measured state, nine gates, delta, change packets, certification, opportunity register). The five L0 pilot briefs in `…/nirmana/l0_assets/` show the shape. Record anything the template does not fit in a "template findings" section.
2. **Measure before you write.** Run the Nikaṣa inspector for L3 only, read-only:
   ```
   mkdir -p /Users/Dev/suvarna/evidence/l3-kshetra-<date>   # absolute: the census runs after a cd
   export PYTHONPATH=/Users/Dev/suvarna/hq/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
   python3 -m suvarna_tracker.census_lock --wait 900 --emit --actor l3-kshetra -- \
     bash -c 'source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/madhav-nikasha && python3 platform/scripts/governance/asset_census.py --layer L3 --out /Users/Dev/suvarna/evidence/l3-kshetra-<date>/census_L3.json'
   ```
   Never pass `--emit-gaps`. Never run it while another full census is running. The ledgers belong to Suvarṇa.
3. **Cover:**
   - the W7 design or the interim clear (per F-1);
   - the stage-3 correctness fixes (axis, per-route null scope, the baseline flag carried through, no L4 read, deterministic tables);
   - the dependency list made true (drop the phantom edges, declare the real reads including Gochara's windows);
   - the pre-registered comparison test, actually run;
   - serving (`query_field_trajectory`, with density contracts per §N.6);
   - `mi_bhara` attaching to the published snapshot only;
   - the real-prior and weight-fitting work;
   - the enrichment target.

   This is the longest path in L3. Order the packets so fixture-proven fixes land first and nothing waits on W7 that doesn't have to.

## 4 · Sealing

1. Review your own draft.
2. Send it to an independent reviewer: a fresh Opus 5.5 agent at high effort, told to break it.
3. Fix what the reviewer finds.
4. Give the native a one-page summary.
5. The native seals it: status `SEALED`, a version and a changelog.
6. Land it on `main` through its own PR, which the native merges.

Nothing is implemented before the seal.

## 5 · Implementation (after the seal)

- **Change packets, as the brief lists them.** Sonnet 5 writes the code (medium effort; high for risky packets). A fresh Opus 5.5 reviewer gates every packet.
- **Standing rules:**
  - the frozen writer contract (CLAUDE.md §N.2);
  - per-chart delete-then-insert (§N.3);
  - surgical migrations, verified as applied, and never edited after they are applied (§N.4);
  - production data changes only through migrations and the orchestrator.
- **Clearing the 8.57 million leftover rows is a destructive operation.** It needs a verified snapshot and the native's approval, and `KshetraReplacementHeld` stays in force until W7 or F-1 says otherwise.
- **The production rebuild waits for** Gochara's new generation live on the canonical chart, and for PR #2731 on `main` (it carries the Kṣetra writer change). PRs to `main` are merged by the native.
- **"Done" means tests pass in production tooling and the inspector's re-measure shows the gates passing.** Suvarṇa re-measures independently (§N.8).

## 6 · Boundaries

- Work in your own worktree: `git worktree add /Users/Dev/madhav-l3/kshetra-final -b l3/kshetra-final origin/main`. The older Kṣetra worktrees and branches are history: read them, don't build on them blindly.
- Do not touch Gochara or Saṅgam code (including the Kṣetra change on the Gochara branch, which lands with #2731), L4 or L5 assets, or the Nikaṣa ledgers. Record anything they need as a finding for the native.
- **Database:** read-only through the project's usual access. Never print or copy credentials, and never call `gcloud` per command.
- **Git:**
  - commit with `git commit -- <paths>`;
  - never use `git add -A`, `--amend` on pushed work, bare `git stash`, rebase or force-push on shared branches.
- **Process:** follow CLAUDE.md, including the session open and close.

## 7 · Report progress to the Suvarṇa tracker, as it happens

The tracker is at http://127.0.0.1:8765. Your items are **F1.K** (the brief, sealed) and **F3.K** (the brief implemented).

```
export PYTHONPATH=/Users/Dev/suvarna/hq/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
python3 -m suvarna_tracker.emit item --actor l3-kshetra --item F1.K --state running --detail "<what you are doing>"
python3 -m suvarna_tracker.emit decision --actor l3-kshetra --decision F-1 --state requested --detail "<options + recommendation>"
python3 -m suvarna_tracker.emit item --actor l3-kshetra --item F1.K --state review --evidence "<sealed brief path + commit>" --detail "sealed by the native; for SEAL-K"
```

- Use `blocked` with a reason whenever you are waiting on the native.
- When the native rules on F-1 or F-4, tell Strategic Suvarṇa; it records the ruling. This session emits only `requested`.
- A `done` without evidence is refused. F1.K reads done only when Strategic Suvarṇa records the seal (SEAL-K); your own events are evidence, not decisions.

## Corrections (v1.1, 2026-09-29)

- **Certification (native decision D2).** A family asset is certified by Suvarṇa's independent re-measure, and only when it was built by an **orchestrator run**, never by a hand-run cutover script. (For Gochara this means no certification until the registered writer produces the new generation.)
- **Rulings.** When the native seals one of this family's rulings, **Strategic Suvarṇa records it** as `decided` in the authoritative decisions log. This session emits `requested` only, never `decided`.
- **One census at a time.** Always run the census through the lock command above; exit code 75 means another census is running: wait and retry.
- **Template revision.** State in the brief's frontmatter which revision of the tier-4 template it follows (it is re-sealed at the engine freeze; Suvarṇa maps briefs to the new revision afterwards).

**Start by:** verifying §1 against the live sources, then telling the native in plain language what differs from this prompt. Then bring the F-1 recommendation.
