---
artifact: L3_FAMILY_CORRECTION_NOTICE
version: "1.3"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1. Once final: published on the campaign-coordination branch for the Pravāha campaign and for any Saṅgam/Kṣetra session the native opens (no native paste)."
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa" (plan item FI-8)
changelog:
  - "1.3 (2026-09-30, v1.5 fold): re-addressed to the Pravāha campaign (steward) and to any Saṅgam/Kṣetra session the native opens; there is no separate L3 Gochara session (fold spec §5). Published on the campaign-coordination branch, no native paste (N-28); FI-8 is no longer an N-1 prerequisite. The acknowledgement is a tracker note whose detail is exactly 'ACK FI-8 notice v1.3' (version-bound). New content: F-3's concrete form (N-32); D2's certification condition with Pravāha's agreement (nothing certifiable until the registered writer produces '5.0'); each campaign's decisions in its own log, Suvarṇa's log citing Pravāha's ids (D-SCOPE, D-41, D-BRIEF, D-CLOUD, D-FLIP, ADK-0029); the nine-gate mapping of Gochara is Suvarṇa's own work; the Gochara prompt retired (superseded by the sealed v3.0 doctrine, D-BRIEF); seals and rulings by Strategic Suvarṇa (N-28); tools from /Users/Dev/suvarna/control (N-37)."
  - "1.2 (2026-09-30, review pass 3): prompts now v1.3. The census runs through the validated wrapper census_run (the lock no longer wraps an arbitrary command); the acknowledgement names notice v1.2 and prompt v1.3."
  - "1.1 (2026-09-29, review pass 2): prompts now v1.2. Absolute evidence folder; tools from the hq worktree; the leftover 'emit it as decided' line removed; the sealed brief reported as review, closed by Strategic Suvarṇa's seal record (SEAL-G/S/K); F-3 now means the cascade removed on all eight foreign keys; an acknowledgement note closes FI-8."
  - "1.0 (2026-09-29): corrections found by Suvarṇa review pass 1, relayed as a report."
---

# Corrections from Strategic Suvarṇa (a report, not an instruction)

**To:** the Pravāha campaign (its steward), and any L3 Saṅgam or L3 Kṣetra session the native opens.
**Where:** published on the campaign-coordination branch (`origin/campaign-coordination`); nobody pastes it.

## For the Pravāha campaign

1. **No prompt of ours applies to you.** The Suvarṇa "L3 Gochara" prompt is retired: your sealed doctrine
   `FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md` is the Gochara final brief (D-BRIEF), and Suvarṇa treats it as satisfying
   its own seal item SEAL-G.
2. **Separate logs.** Each campaign records its own rulings in its own log. Suvarṇa's decisions log records only
   Suvarṇa decisions, written only by Strategic Suvarṇa; for Gochara facts it cites your ids (D-SCOPE, D-41, D-BRIEF,
   D-CLOUD, D-FLIP, ADK-0029). Suvarṇa's tracker reads your item states (B0.2, J2, A1.2, A5.3, A5.6, A6.1, A6.2) from
   your tracker's `/api/state` (a read-only `peer_tracker_item` detector); it never asks you to emit into ours beyond
   the acknowledgement below.
3. **Certification (D2), as you agreed.** A Gochara asset is certified by Suvarṇa's independent re-measure, and only
   when built by an **orchestrator run** of the registered writer, never by a cutover script: nothing is certifiable
   until the registered writer produces `'5.0'`.
4. **The nine-gate mapping is ours.** Mapping your doctrine onto the tier-4 template's nine gates is Suvarṇa's own
   L3 analysis (A.L3); it is never required of you.
5. **F-3 (for information; no Gochara table is among the keys).** See §F-3 below.

## For a Saṅgam or Kṣetra session the native opens

Your prompt is `…/briefs/suvarna/prompts/L3_<SANGAM|KSHETRA>_FINAL_BRIEF_PROMPT_v1_0.md` at v1.4 (under
`/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/`). What changed since v1.3:

1. **Seals and rulings are Strategic Suvarṇa's (N-28).** It decides F-1, F-2, F-4 and F-6 on your recommendation and
   seals your brief (SEAL-S, SEAL-K). You record your own decisions only in your own log and emit only `requested` and
   `review` to Suvarṇa's tracker, never `decided` or a sealed `done`.
2. **Implementation ownership is decided at J1 (J1.FO).** A session that has acknowledged this notice or committed on
   its family branches owns implementation, and charter R8 then protects it; otherwise Suvarṇa implements.
3. **Certification (D2):** as in item 3 above; your assets also wait for `'5.0'` served on the canonical chart.
4. **Inputs:** Pravāha's consumer contract
   `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/L3_FAMILY_COORDINATION_v1_0.md`.
5. **The census** runs only through the wrapper, with an absolute `--out` (exit 75 = another census is running; wait):
   ```
   mkdir -p /Users/Dev/suvarna/evidence/l3-<family>-<date>
   export PYTHONPATH=/Users/Dev/suvarna/control/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
   python3 -m suvarna_tracker.census_run --layer L3 --out /Users/Dev/suvarna/evidence/l3-<family>-<date>/census_L3.json \
     --wait 900 --emit --actor l3-<family>
   ```
6. **Destructive operations** need a rebuild plan, a serving guard and recorded pre-op fingerprints/counts (N-29, N-33),
   not a snapshot and not the native's approval.
7. **Saṅgam only.** Your unapplied migrations are 1088, 1089, 1090, 1092 and 1093; 1091 is Gochara's and is applied.

## F-3 (decided, N-32)

Eight `ON DELETE CASCADE` foreign keys point at `bodha_msr_signals` (from `kala_convergence`, `kala_darshana`,
`kala_bhavishya`, `kala_activation`, `kala_obstruction`, `bodha_signal_embeddings`, `bodha_contradictions` ×2).
Suvarṇa's Track E migration **drops all eight** (target: no foreign key) and replaces `assert_l2_msr_delete_safe` so it
never refuses (it keeps its admitted-asset-context check and records referencing-row counts as build evidence).
Derived rows are regenerable: the downstream is rebuilt in wave order, and the owner of `kala_convergence` is notified by
lease note before the migration and before each L2 MSR wave. `ON DELETE SET NULL` was rejected: 4 of the 8 columns are
NOT NULL (measured 2026-09-30). `kala_convergence`'s own downstream cascades (into `kala_darshana`, `kala_obstruction`,
`phala_anchors`, and on to `phala_*`) stay; each wave's impact statement lists them.

## Acknowledge

Once you have read this, emit one tracker note whose detail is exactly `ACK FI-8 notice v1.3` (the version is part of
it; an acknowledgement of an earlier version does not count):
```
export PYTHONPATH=/Users/Dev/suvarna/control/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
python3 -m suvarna_tracker.emit note --actor <pravaha|l3-sangam|l3-kshetra> --detail "ACK FI-8 notice v1.3"
```

If anything you have already done conflicts with this, tell Strategic Suvarṇa; nothing here asks you to undo work.
