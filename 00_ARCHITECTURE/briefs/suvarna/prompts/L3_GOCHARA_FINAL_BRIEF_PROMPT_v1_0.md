---
artifact: L3_GOCHARA_FINAL_BRIEF_PROMPT
version: "1.2"
status: READY — paste into the Gochara conversation
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.2 (2026-09-29, review pass 2 / FI-8): the leftover line telling this session to emit a ruling as decided is removed (its own Corrections forbid it); the sealed brief is reported as review with evidence, and F1.G closes when Strategic Suvarṇa records the native's seal (SEAL-G); the evidence folder is an absolute path under /Users/Dev/suvarna/evidence; the tools run from the hq worktree; F-3 means the cascade removed from all eight keys."
  - "1.1 (2026-09-29, review pass 1 / FI-8): census command corrected (--out is a file; the read-only credential is sourced; runs through the census lock so only one census runs at a time); certification condition (D2); native rulings are recorded as decided only by Strategic Suvarṇa; record the tier-4 template revision the brief follows."
  - "1.0 (2026-09-29): first issue, on the native's instruction that each L3 focus family gets its own session to seal a final brief and implement it."
---

# L3 Gochara — seal the final brief, then implement it

**Session name:** L3 Gochara. You own the Gochara family end to end: a final brief the native seals, then its implementation. The Suvarṇa campaign will not change Gochara code; its L3 analysis will evaluate whatever you have produced most recently.

## 1 · Where things stand (verify every line before relying on it)

- **Assets:** `ka_gochara` (windows), `ka_gochara_resonance`, `ka_vedha_gochara`. Inactive: `ka_gochara_v3_century_materialize` (the century writer, held), `ka_gochara_sweep` (retired). L0 inputs: `bg_gochara_arcs`, `bg_gochara_citation_resolution`.
- **Served today:** generation `'3.0'` (1984–2084) on both charts (`482012f1…`, `1c826d5a…`), via `kala_gochara_authority`.
- **The live lane** (a Kimi session) works on branch `l3/gochara-autonomous-wp0-7`, worktree `/Users/Dev/madhav-l3/gochara-wp0-7`, PR #2731. Its register is `00_ARCHITECTURE/autonomy/ADHIKARIN_RULINGS.md` on that branch.
- **ADK-0027 is binding.** On 2026-09-28 the lane switched chart `482012f1` to `'4.0'` (19:22 UTC) before the deploy-before-switch directive (F-0) arrived, and reversed it at 19:29 UTC. `'4.0'` is retired as a label. It then merged `main` in (`f95cf19af`) and launched a full-century rebuild under `'4.1'` on a disposable rehearsal database (`8e1fed557`, `ec4c35110`).
- **The native has put the Gochara execution on hold** while reviewing the plan. Do not restart the lane, and do not switch authority on any chart, without the native's word.
- **Known gaps** (the full list, with sources, is in the reconciliation report):
  - R240: the registered writer still produces `_v2` / `'2.0'`, so the Build button cannot produce the new generation;
  - registry, seed and writer disagree;
  - resonance defects R-1 to R-6;
  - overlays cover only about 460 days;
  - `main`'s writers would wipe the new stamp columns;
  - the bindu matrix and the Moon channel are not built;
  - `'4.0'` scoring lost variation (promise 1.0 everywhere, fixed permission, tārā skipped, vedha covering about 15 months);
  - an out-of-horizon query must never come back silently empty.

**Read first:**
1. `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/l3_recon/GOCHARA_RECON.md` (the current state, with a source for every claim; §5 is the "fully enriched" target).
2. `/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` §1 and §4 (the links to Saṅgam and Kṣetra).
3. ADK-0027 in the lane's register.
4. Your family's own design documents, as cited in the reconciliation report.

## 2 · The brief

Write `00_ARCHITECTURE/briefs/l3_families/GOCHARA_FINAL_BRIEF_v1_0.md`. It covers every Gochara asset.

1. **Follow the asset elevation template:** `/Users/Dev/madhav-nikasha/00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md` (identity, measured state, nine gates, delta, change packets, certification, opportunity register). The five L0 pilot briefs in `…/nirmana/l0_assets/` show the shape. If the template does not fit something, say so in a "template findings" section; do not bend it silently.
2. **Measure before you write.** Run the Nikaṣa inspector for L3 only, read-only:
   ```
   mkdir -p /Users/Dev/suvarna/evidence/l3-gochara-<date>   # absolute: the census runs after a cd
   export PYTHONPATH=/Users/Dev/suvarna/hq/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
   python3 -m suvarna_tracker.census_lock --wait 900 --emit --actor l3-gochara -- \
     bash -c 'source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/madhav-nikasha && python3 platform/scripts/governance/asset_census.py --layer L3 --out /Users/Dev/suvarna/evidence/l3-gochara-<date>/census_L3.json'
   ```
   Never pass `--emit-gaps`. Never run it while another full census is running. The gap and certification ledgers belong to Suvarṇa.
3. **Absorb the lane, don't replace it.** Its remaining ADK-0027 steps (century candidate, readiness packet, the native's merge and deploy of #2731, the `env.DEPLOY_SHA` check, the switch with trigger #0, the soaks) become the brief's first packets.
4. **Then the rest:**
   - the orchestrator writer that produces the new generation for any chart (closing R240);
   - registry and seed alignment;
   - retiring the century writer;
   - the resonance, overlay, stamp, bindu and Moon work;
   - scoring that keeps its variation;
   - serving with honest provenance and no silent empties;
   - the enrichment target.
5. **Publish the interface Saṅgam and Kṣetra will read:** table, generation label, authority filter and horizon. Tell the native when it changes.
6. **Bring rulings to the native, not assumptions.** Each ruling comes with options, a recommendation and its consequence.

## 3 · Sealing

1. Review your own draft.
2. Send it to an independent reviewer: a fresh Opus 5.5 agent at high effort, told to break it.
3. Fix what the reviewer finds.
4. Give the native a one-page summary.
5. The native seals it: status `SEALED`, a version and a changelog.
6. Land the sealed brief on `main` through its own PR, which the native merges.

Nothing is implemented before the seal, except the lane's in-flight steps, and only when the native lifts the hold.

## 4 · Implementation (after the seal)

- **Change packets, as the brief lists them.** Sonnet 5 writes the code (medium effort; high for risky packets). A fresh Opus 5.5 reviewer gates every packet before it counts.
- **Standing rules:**
  - the frozen writer contract (CLAUDE.md §N.2);
  - per-chart delete-then-insert (§N.3);
  - surgical migrations, verified as applied, and never edited after they are applied (§N.4);
  - production data changes only through migrations and the orchestrator;
  - any clear of populated data needs a verified snapshot and the native's approval;
  - PRs to `main` are merged by the native.
- **"Done" means tests pass in production tooling and the inspector's re-measure shows the gates passing.** Suvarṇa re-measures independently; your claims are evidence, not verdicts (§N.8).

## 5 · Boundaries

- Work in your own worktree: `git worktree add /Users/Dev/madhav-l3/gochara-final -b l3/gochara-final origin/main`.
- The lane's branch is the lane's. Change it only through the lane, and only with the native's word.
- Do not touch Saṅgam or Kṣetra code, L0 or L2 assets, or the Nikaṣa ledgers. Record anything they need as a finding for the native.
- **Database:** read-only through the project's usual access. Never print or copy credentials, and never call `gcloud` per command.
- **Git:**
  - commit with `git commit -- <paths>`;
  - never use `git add -A`, `--amend` on pushed work, bare `git stash`, rebase or force-push on shared branches.
- **Process:** follow CLAUDE.md, including the session open and close.

## 6 · Report progress to the Suvarṇa tracker, as it happens

The tracker is at http://127.0.0.1:8765. Your items are **F1.G** (the brief, sealed) and **F3.G** (the brief implemented).

```
export PYTHONPATH=/Users/Dev/suvarna/hq/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
python3 -m suvarna_tracker.emit item --actor l3-gochara --item F1.G --state running --detail "<what you are doing>"
python3 -m suvarna_tracker.emit item --actor l3-gochara --item F1.G --state review --detail "independent review"
python3 -m suvarna_tracker.emit item --actor l3-gochara --item F1.G --state review --evidence "<sealed brief path + commit>" --detail "sealed by the native; for SEAL-G"
```

- Use `blocked` with a reason whenever you are waiting on the native.
- The lane's steps are F2.1–F2.5. Emit them when they move, with the commit as evidence.
- A `done` without evidence is refused. F1.G reads done only when Strategic Suvarṇa records the seal (SEAL-G); your own events are evidence, not decisions.

## Corrections (v1.1, 2026-09-29)

- **Certification (native decision D2).** A family asset is certified by Suvarṇa's independent re-measure, and only when it was built by an **orchestrator run**, never by a hand-run cutover script. (For Gochara this means no certification until the registered writer produces the new generation.)
- **Rulings.** When the native seals one of this family's rulings, **Strategic Suvarṇa records it** as `decided` in the authoritative decisions log. This session emits `requested` only, never `decided`.
- **One census at a time.** Always run the census through the lock command above; exit code 75 means another census is running: wait and retry.
- **Template revision.** State in the brief's frontmatter which revision of the tier-4 template it follows (it is re-sealed at the engine freeze; Suvarṇa maps briefs to the new revision afterwards).

**Start by:** verifying §1 against the live sources, then telling the native in plain language what differs from this prompt, before writing anything.
