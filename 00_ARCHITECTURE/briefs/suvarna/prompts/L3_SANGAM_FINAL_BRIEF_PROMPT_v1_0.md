---
artifact: L3_SANGAM_FINAL_BRIEF_PROMPT
version: "1.4"
status: "KEPT — used only if the native opens such a session; otherwise Suvarṇa's Architect-led Track F lanes use the same content as their lane brief. PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.4 (2026-09-30, v1.5 fold): kept, used only if the native opens an L3 Saṅgam session; otherwise the lane brief of Suvarṇa's Track F Architect lanes (fold spec §5). Rulings and the seal are Strategic Suvarṇa's (N-28: F-2/F-6 decided by SS on this session's recommendation; SEAL-S); each campaign records decisions only in its own log, and only SS writes Suvarṇa's. F-3 decided (N-32: all eight FKs dropped, target no_fk; the delete guard never refuses; downstream rebuilt in wave order; SET NULL rejected, 4 of 8 columns NOT NULL). Gochara = the Pravāha campaign; '5.0' (D-41), 482012f1 only (D-SCOPE); Pravāha's L3_FAMILY_COORDINATION_v1_0.md is an input. Implementation ownership at J1 (J1.FO). Destructive ops per N-29/N-33; merges through merge_gate (N-25b, N-38); tools from /Users/Dev/suvarna/control (N-37); census via census_run."
  - "1.3 (2026-09-30, review pass 3 / FI-8): the census runs through the validated wrapper python3 -m suvarna_tracker.census_run --layer L3 --out <absolute path> (census_lock no longer wraps an arbitrary command, review pass 3 B6); Corrections updated to match."
  - "1.2 (2026-09-29, review pass 2 / FI-8): the leftover line telling this session to emit a ruling as decided is removed (its own Corrections forbid it); the sealed brief is reported as review with evidence, and F1.S closes when Strategic Suvarṇa records the native's seal (SEAL-S); the evidence folder is an absolute path under /Users/Dev/suvarna/evidence; the tools run from the hq worktree; F-3 means the cascade removed from all eight keys."
  - "1.1 (2026-09-29, review pass 1 / FI-8): census command corrected (--out is a file; the read-only credential is sourced; runs through the census lock so only one census runs at a time); certification condition (D2); native rulings are recorded as decided only by Strategic Suvarṇa; record the tier-4 template revision the brief follows."
  - "1.0 (2026-09-29): first issue, on the native's instruction that each L3 focus family gets its own session to seal a final brief and implement it."
---

# L3 Saṅgam — seal the final brief, then implement it

**Use (v1.4).** This prompt is used only if the native opens an L3 Saṅgam session. Otherwise Suvarṇa's Track F
Architect lanes use the same content as their lane brief (design: the final brief, F1.S). Wherever it says "this
session", read "the lane" in that case.

**Session name:** L3 Saṅgam. You own the Saṅgam design: a final brief that Strategic Suvarṇa seals (SEAL-S, N-28).
**Implementation ownership is decided by Strategic Suvarṇa at J1 (J1.FO):** a family session that has acknowledged the
correction notice (FI-8) or shown commits on `sangam/*` branches owns implementation, and charter R8 then protects it;
otherwise the Suvarṇa swarm implements it as ordinary Track I/B work.

## 1 · Where things stand (verify every line before relying on it)

- **Asset:** `ka_sangam` → `kala_convergence`.
  - Eleven upstream assets, including `ka_gochara`, `ka_yojaka`, `ka_dasha_kala` and `bo_laksana`.
  - Main reader: `ka_kala_darshana`.
  - Eight open Nikaṣa gaps. Nirmāṇa never froze it.
- **0 rows on the canonical chart** `482012f1…`.
  - `kala_convergence.signal_id` cascades on delete from `bodha_msr_signals`, so the `bo_laksana` rebuild of 2026-09-08 almost certainly wiped it. Four sibling `kala_*` tables with the same link are also empty.
  - The only rows left are pre-September: 17,957 on `1c826d5a…` and 2,540 on `cb73cd3d…` (Mode D only).
- **Stage 3** (branch `sangam/stage3`) is unmerged. The consolidation PR #2735 conflicts and fails four CI checks, and its migrations (1088, 1089, 1090, 1092, 1093) are not applied (1091 belongs to Gochara, now the Pravāha campaign, and is applied). The independent review said "conforms with amendments", with one high-severity item: the aṣṭakavarga check depends on data no writer produces.
- **Stage 4** was written but never run.
- **Known defects:**
  - Modes A and B measure every contact against 0° Aries (no target longitude; dosha predicates get none even in stage 3);
  - stage-3 rows carry `peak_date = NULL`, which `main` rejects;
  - the episode grouping key omits `mode`;
  - Mode D is 80% of rows (the same 478 windows repeated for 25 predicates);
  - several scoring inputs are always empty;
  - no stage-3 test touches a database;
  - `ka_yojaka` is stale (79 canonical predicates point at signals that no longer exist) and must be rebuilt first.
- **Upstream Gochara is changing.** Gochara is run by the **Pravāha campaign** (tracker http://127.0.0.1:8766). It moves from `'3.0'` to a new full-century generation labelled **`'5.0'`** (D-41), built for `482012f1` only (D-SCOPE), and Saṅgam must be rebuilt on it. PR #2731 merged 2026-09-30 as `285bff17c`. Pravāha's consumer contract states the interface (the three objects, frames, coverage, lineage).

**Read first:**
1. `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/l3_recon/SANGAM_RECON.md` (the current state, with a source for every claim).
2. `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` (v1.4) §2 and §4.
3. Pravāha's consumer contract `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/L3_FAMILY_COORDINATION_v1_0.md` (an input to the brief).
4. The family's own design documents, as cited in the reconciliation report: `SANGAM_ELEVATION_BRIEF_v1_0.md`, `SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md`, `SANGAM_STAGE3_STATE.md`, `SANGAM_STAGE4_STATE.md`, `DK_REVIEW_SANGAM_204b003ea_v1_0.md`.
5. The ŚAḌ-DARŚANA brief (`SHAD_DARSHANA_BRIEF_v2_0.md`) and `KALA_TRANSFORMATION_HANDOFF_v1_0.md`.

## 2 · Settle these first, before designing anything

Your brief brings each of these rulings to Strategic Suvarṇa, with options, a recommendation and its consequence; Strategic Suvarṇa decides on that recommendation (N-28):

- **F-2 — keep and improve Saṅgam, or retire it into `kala_field`.** ŚAḌ-DARŚANA planned to retire it; the elevation plan invests in it instead. This decides everything else. `kala_field` is Kṣetra's table, so agree the answer with whoever designs Kṣetra (a Kṣetra session, or Track F's Kṣetra lane) before recommending it.
- **F-6 — the Mode D design.** Today it is 80% of rows, one set of windows repeated.
- **F-3 is decided (N-32); design to it.** Eight `ON DELETE CASCADE` foreign keys point at `bodha_msr_signals` (from `kala_convergence`, `kala_darshana`, `kala_bhavishya`, `kala_activation`, `kala_obstruction`, `bodha_signal_embeddings`, `bodha_contradictions` ×2). Suvarṇa's Track E migration drops all eight (target `no_fk`) and replaces `assert_l2_msr_delete_safe` so it never refuses (it records referencing-row counts as build evidence). Signal ids are deterministic, so unchanged signals keep their references; changed or removed ones leave dangling references until the downstream rebuilds in its own wave (the serving guard covers the gap). `ON DELETE SET NULL` was rejected: 4 of the 8 columns are NOT NULL (`bodha_contradictions.signal_a_id`, `.signal_b_id`, `bodha_signal_embeddings.signal_id`, `kala_activation.signal_id`; measured 2026-09-30). `kala_convergence`'s own downstream cascades stay (into `kala_darshana`, `kala_obstruction`, `phala_anchors`; SET NULL into `kala_bhavishya`). The Saṅgam owner is notified by lease note before the migration and before each L2 MSR wave; the brief must say how Saṅgam tolerates dangling `signal_id`s between waves.

## 3 · The brief

Write `00_ARCHITECTURE/briefs/l3_families/SANGAM_FINAL_BRIEF_v1_0.md`.

1. **Follow the asset elevation template:** `/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` (identity, measured state, nine gates, delta, change packets, certification, opportunity register). The five L0 pilot briefs in `…/nirmana/l0_assets/` show the shape. Record anything the template does not fit in a "template findings" section.
2. **Measure before you write.** Run the Nikaṣa inspector for L3 only, read-only:
   ```
   mkdir -p /Users/Dev/suvarna/evidence/l3-sangam-<date>   # --out must be an absolute path; create the folder first
   export PYTHONPATH=/Users/Dev/suvarna/control/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
   python3 -m suvarna_tracker.census_run --layer L3 --out /Users/Dev/suvarna/evidence/l3-sangam-<date>/census_L3.json \
     --wait 900 --emit --actor l3-sangam
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
4. Give Strategic Suvarṇa a one-page summary with the reviewer's findings and their disposition.
5. Strategic Suvarṇa seals it (SEAL-S, N-28): status `SEALED`, a version and a changelog.
6. Land it on `main` through its own PR (a Suvarṇa lane merges through the merge gate, N-25b, N-38).

Nothing is implemented before the seal.

## 5 · Implementation (after the seal)

- **Change packets, as the brief lists them.** Sonnet 5 writes the code (medium effort; high for risky packets). A fresh Opus 5.5 reviewer gates every packet.
- **Standing rules:**
  - the frozen writer contract (CLAUDE.md §N.2);
  - per-chart delete-then-insert (§N.3);
  - surgical migrations, verified as applied, and never edited after they are applied (§N.4);
  - production data changes only through migrations and the orchestrator;
  - a destructive operation needs a rebuild plan, a serving guard and recorded pre-op fingerprints/counts, and a Strategic Suvarṇa decision beyond a writer's own delete-then-insert (N-29, N-33); no dumps;
  - PRs to `main` merge through the merge gate (N-25b, N-38).
- **The production rebuild waits for two things:** Gochara's `'5.0'` live on the canonical chart (Pravāha A6.1, gated on its N-FLIP), and F-3's migration applied (F3.FK, F3.GUARD, F3.PROOF).
- **"Done" means tests pass in production tooling and the inspector's re-measure shows the gates passing.** Suvarṇa re-measures independently (§N.8).

## 6 · Boundaries

- Work in your own worktree: `git worktree add /Users/Dev/madhav-l3/sangam-final -b l3/sangam-final origin/main` (a Suvarṇa lane uses its own lane worktree). Bring over what stage 3 got right deliberately; don't inherit its branch.
- Do not touch Gochara (Pravāha's) or Kṣetra code, L2 assets, or the Nikaṣa ledgers. Record anything they need as a finding for Strategic Suvarṇa.
- **Database:** read-only through the project's usual access. Never print or copy credentials, and never call `gcloud` per command.
- **Git:**
  - commit with `git commit -- <paths>`;
  - never use `git add -A`, `--amend` on pushed work, bare `git stash`, rebase or force-push on shared branches.
- **Process:** follow CLAUDE.md, including the session open and close.

## 7 · Report progress to the Suvarṇa tracker, as it happens

The tracker is at http://127.0.0.1:8765. Your items are **F1.S** (the brief, sealed) and **F3.S** (the brief implemented).

```
export PYTHONPATH=/Users/Dev/suvarna/control/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
python3 -m suvarna_tracker.emit item --actor l3-sangam --item F1.S --state running --detail "<what you are doing>"
python3 -m suvarna_tracker.emit decision --actor l3-sangam --decision F-2 --state requested --detail "<options + recommendation>"
python3 -m suvarna_tracker.emit item --actor l3-sangam --item F1.S --state review --evidence "<brief path + commit>" --detail "reviewed; for SEAL-S"
```

- Use `blocked` with a reason whenever you are waiting on a decision.
- Strategic Suvarṇa decides F-2 and F-6 on your recommendation and records them in Suvarṇa's log (`$SUVARNA_HOME/authority/DECISIONS.jsonl`); nobody else writes that log. A native-opened session records its own decisions only in its own log and emits only `requested` here.
- A `done` without evidence is refused. F1.S reads done only when Strategic Suvarṇa records the seal (SEAL-S); your own events are evidence, not decisions.

## Corrections (v1.1, 2026-09-29; census wording updated in v1.3, 2026-09-30; rulings and seals updated in v1.4, 2026-09-30)

- **Certification (D2).** A family asset is certified by Suvarṇa's independent re-measure, and only when it was built by an **orchestrator run**, never by a hand-run cutover script. (For Gochara, Pravāha agreed: nothing is certifiable until the registered writer produces `'5.0'`.)
- **Rulings and seals (v1.4, N-28).** Strategic Suvarṇa decides this family's rulings on the owning session's recommendation (or from Track F's own design lanes) and seals the brief; it alone records them as `decided` in Suvarṇa's decisions log. This session emits `requested` only, never `decided`.
- **One census at a time.** Always run the census with the `census_run` command above (it takes the census lock itself); exit code 75 means another census is running: wait and retry.
- **The census command (v1.3).** The census now runs through the wrapper `python3 -m suvarna_tracker.census_run --layer L3 --out <absolute path>`, which takes the lock, sources the read-only credential and runs only the inspector. The earlier form, `census_lock … -- bash -c '…'`, is retired: the lock no longer wraps an arbitrary command.
- **Template revision.** State in the brief's frontmatter which revision of the tier-4 template it follows (it is re-sealed at the engine freeze; Suvarṇa maps briefs to the new revision afterwards).

**Start by:** verifying §1 against the live sources, then reporting to Strategic Suvarṇa (a tracker note) what differs from this prompt. Then bring the F-2 recommendation.
