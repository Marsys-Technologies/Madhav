---
artifact: L3_SANGAM_FINAL_BRIEF_PROMPT
version: "1.1"
status: READY — paste into a new conversation
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.1 (2026-09-29, review pass 1 / FI-8): census command corrected (--out is a file; the read-only credential is sourced; runs through the census lock so only one census runs at a time); certification condition (D2); native rulings are recorded as decided only by Strategic Suvarṇa; record the tier-4 template revision the brief follows."
  - "1.0 (2026-09-29): first issue, on the native's instruction that each L3 focus family gets its own session to seal a final brief and implement it."
---

# L3 Saṅgam — seal the final brief, then implement it

**Session name:** L3 Saṅgam. You own the Saṅgam family end to end: a final brief the native seals, then its implementation. The Suvarṇa campaign will not change Saṅgam code; its L3 analysis will evaluate whatever you have produced most recently.

## 1 · Where things stand (verify every line before relying on it)

- **Asset:** `ka_sangam` → `kala_convergence`.
  - Eleven upstream assets, including `ka_gochara`, `ka_yojaka`, `ka_dasha_kala` and `bo_laksana`.
  - Main reader: `ka_kala_darshana`.
  - Eight open Nikaṣa gaps. Nirmāṇa never froze it.
- **0 rows on the canonical chart** `482012f1…`.
  - `kala_convergence.signal_id` cascades on delete from `bodha_msr_signals`, so the `bo_laksana` rebuild of 2026-09-08 almost certainly wiped it. Four sibling `kala_*` tables with the same link are also empty.
  - The only rows left are pre-September: 17,957 on `1c826d5a…` and 2,540 on `cb73cd3d…` (Mode D only).
- **Stage 3** (branch `sangam/stage3`) is unmerged. The consolidation PR #2735 conflicts and fails four CI checks, and its migrations (1088, 1089, 1090, 1092, 1093) are not applied (1091 belongs to the Gochara lane and is applied). The independent review said "conforms with amendments", with one high-severity item: the aṣṭakavarga check depends on data no writer produces.
- **Stage 4** was written but never run.
- **Known defects:**
  - Modes A and B measure every contact against 0° Aries (no target longitude; dosha predicates get none even in stage 3);
  - stage-3 rows carry `peak_date = NULL`, which `main` rejects;
  - the episode grouping key omits `mode`;
  - Mode D is 80% of rows (the same 478 windows repeated for 25 predicates);
  - several scoring inputs are always empty;
  - no stage-3 test touches a database;
  - `ka_yojaka` is stale (79 canonical predicates point at signals that no longer exist) and must be rebuilt first.
- **Upstream Gochara is changing.** It moves from `'3.0'` to a new full-century generation, and Saṅgam must be rebuilt on it. The L3 Gochara session publishes the interface (table, generation, authority filter, horizon).

**Read first:**
1. `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/l3_recon/SANGAM_RECON.md` (the current state, with a source for every claim).
2. `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` §2 and §4.
3. The family's own design documents, as cited in the reconciliation report: `SANGAM_ELEVATION_BRIEF_v1_0.md`, `SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md`, `SANGAM_STAGE3_STATE.md`, `SANGAM_STAGE4_STATE.md`, `DK_REVIEW_SANGAM_204b003ea_v1_0.md`.
4. The ŚAḌ-DARŚANA brief (`SHAD_DARSHANA_BRIEF_v2_0.md`) and `KALA_TRANSFORMATION_HANDOFF_v1_0.md`.

## 2 · Settle these first, before designing anything

Your brief brings each of these rulings to the native, with options, a recommendation and its consequence:

- **F-2 — keep and improve Saṅgam, or retire it into `kala_field`.** ŚAḌ-DARŚANA planned to retire it; the elevation plan invests in it instead. This decides everything else. `kala_field` is Kṣetra's table, so agree the answer with the L3 Kṣetra session before recommending it.
- **F-6 — the Mode D design.** Today it is 80% of rows, one set of windows repeated.
- **F-3 — the L2↔L3 cascade lock.** Every L2 re-elevation either wipes Saṅgam, or is refused by it once Saṅgam is rebuilt (register R243). Propose a foreign-key change or a sequencing rule. This binds L2 as well, so Suvarṇa waits for this ruling before rebuilding any L2 MSR asset.

## 3 · The brief

Write `00_ARCHITECTURE/briefs/l3_families/SANGAM_FINAL_BRIEF_v1_0.md`.

1. **Follow the asset elevation template:** `/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` (identity, measured state, nine gates, delta, change packets, certification, opportunity register). The five L0 pilot briefs in `…/nirmana/l0_assets/` show the shape. Record anything the template does not fit in a "template findings" section.
2. **Measure before you write.** Run the Nikaṣa inspector for L3 only, read-only:
   ```
   mkdir -p <your evidence folder>
   export PYTHONPATH=/Users/Dev/madhav-suvarna-plan/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
   python3 -m suvarna_tracker.census_lock --wait 900 --emit --actor l3-sangam -- \
     bash -c 'source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/madhav-nikasha && python3 platform/scripts/governance/asset_census.py --layer L3 --out <your evidence folder>/census_L3.json'
   ```
   Never pass `--emit-gaps`. Never run it while another full census is running. The ledgers belong to Suvarṇa.
3. **Cover, per the F-2 outcome:**
   - the `ka_yojaka` rebuild as a prerequisite;
   - the target-point fix for every mode;
   - `peak_date` and the grouping key;
   - the stage-3 salvage or replacement (and what happens to PR #2735);
   - scores comparable across modes;
   - reusing Gochara's episode finder;
   - retiring `confidence_*` across its five readers;
   - the output-contract columns;
   - density contracts on the two serving modules (§N.6);
   - tests that touch a real test database;
   - the enrichment target.

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
  - production data changes only through migrations and the orchestrator;
  - any clear of populated data needs a verified snapshot and the native's approval;
  - PRs to `main` are merged by the native.
- **The production rebuild waits for two things:** Gochara's new generation live on the canonical chart, and ruling F-3.
- **"Done" means tests pass in production tooling and the inspector's re-measure shows the gates passing.** Suvarṇa re-measures independently (§N.8).

## 6 · Boundaries

- Work in your own worktree: `git worktree add /Users/Dev/madhav-l3/sangam-final -b l3/sangam-final origin/main`. Bring over what stage 3 got right deliberately; don't inherit its branch.
- Do not touch Gochara or Kṣetra code, L2 assets, or the Nikaṣa ledgers. Record anything they need as a finding for the native.
- **Database:** read-only through the project's usual access. Never print or copy credentials, and never call `gcloud` per command.
- **Git:**
  - commit with `git commit -- <paths>`;
  - never use `git add -A`, `--amend` on pushed work, bare `git stash`, rebase or force-push on shared branches.
- **Process:** follow CLAUDE.md, including the session open and close.

## 7 · Report progress to the Suvarṇa tracker, as it happens

The tracker is at http://127.0.0.1:8765. Your items are **F1.S** (the brief, sealed) and **F3.S** (the brief implemented).

```
export PYTHONPATH=/Users/Dev/madhav-suvarna-plan/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
python3 -m suvarna_tracker.emit item --actor l3-sangam --item F1.S --state running --detail "<what you are doing>"
python3 -m suvarna_tracker.emit decision --actor l3-sangam --decision F-2 --state requested --detail "<options + recommendation>"
python3 -m suvarna_tracker.emit item --actor l3-sangam --item F1.S --state done --evidence "<sealed brief path + commit>"
```

- Use `blocked` with a reason whenever you are waiting on the native.
- When the native rules on F-2, F-6 or F-3, emit it as `decided` with what was decided.
- A `done` without evidence is refused.

## Corrections (v1.1, 2026-09-29)

- **Certification (native decision D2).** A family asset is certified by Suvarṇa's independent re-measure, and only when it was built by an **orchestrator run**, never by a hand-run cutover script. (For Gochara this means no certification until the registered writer produces the new generation.)
- **Rulings.** When the native seals one of this family's rulings, **Strategic Suvarṇa records it** as `decided` in the authoritative decisions log. This session emits `requested` only, never `decided`.
- **One census at a time.** Always run the census through the lock command above; exit code 75 means another census is running: wait and retry.
- **Template revision.** State in the brief's frontmatter which revision of the tier-4 template it follows (it is re-sealed at the engine freeze; Suvarṇa maps briefs to the new revision afterwards).

**Start by:** verifying §1 against the live sources, then telling the native in plain language what differs from this prompt. Then bring the F-2 recommendation.
