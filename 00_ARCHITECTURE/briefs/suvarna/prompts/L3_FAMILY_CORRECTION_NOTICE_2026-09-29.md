---
artifact: L3_FAMILY_CORRECTION_NOTICE
version: "1.2"
status: READY — paste into each L3 family session (Gochara, Saṅgam, Kṣetra)
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa" (plan item FI-8)
changelog:
  - "1.2 (2026-09-30, review pass 3): prompts now v1.3. The census runs through the validated wrapper census_run (the lock no longer wraps an arbitrary command); the acknowledgement names notice v1.2 and prompt v1.3."
  - "1.1 (2026-09-29, review pass 2): prompts now v1.2. Absolute evidence folder; tools from the hq worktree; the leftover 'emit it as decided' line removed; the sealed brief reported as review, closed by Strategic Suvarṇa's seal record (SEAL-G/S/K); F-3 now means the cascade removed on all eight foreign keys; an acknowledgement note closes FI-8."
  - "1.0 (2026-09-29): corrections found by Suvarṇa review pass 1, relayed as a report."
---

# Corrections to your start prompt (a report from Strategic Suvarṇa, not a new instruction)

Your prompt has been corrected to v1.3. Please re-read it:
`/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/prompts/L3_<GOCHARA|SANGAM|KSHETRA>_FINAL_BRIEF_PROMPT_v1_0.md`

What changed:

1. **The census command.** The census runs through one validated wrapper, which takes the lock, sources the read-only
   credential and runs only the inspector. `--out` must be a file at an **absolute** path; create the folder first.
   From any folder:
   ```
   mkdir -p /Users/Dev/suvarna/evidence/l3-<family>-<date>
   export PYTHONPATH=/Users/Dev/suvarna/hq/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
   python3 -m suvarna_tracker.census_run --layer L3 --out /Users/Dev/suvarna/evidence/l3-<family>-<date>/census_L3.json \
     --wait 900 --emit --actor l3-<family>
   ```
   The lock makes sure only one census runs at a time across all sessions (exit 75 = another census is running; wait
   and retry). The earlier `census_lock … -- bash -c '…'` form (notice v1.1, prompts v1.2) is retired.
2. **Certification (native decision D2).** Your assets are certified by Suvarṇa's independent re-measure, and only if
   they were built by an **orchestrator run**, never by a hand-run cutover script. For Gochara: no certification until
   the registered writer produces the new generation.
3. **Rulings.** When the native seals one of your family's rulings (F-1…F-6), Strategic Suvarṇa records it as `decided`
   in the authoritative decisions log. Your session emits `requested` only, never `decided`. (v1.1 of your prompt still
   had one line saying otherwise; it is removed.)
4. **Your sealed brief.** Report it as `review` with the sealed path and commit as evidence. F1.G/F1.S/F1.K close when
   Strategic Suvarṇa records the native's seal (SEAL-G, SEAL-S, SEAL-K).
5. **Template revision.** Write in your brief's frontmatter which revision of the tier-4 template it follows. The
   template is re-sealed at the engine freeze, and Suvarṇa maps briefs to the new revision afterwards.
6. **F-3 (for Saṅgam; for information to the others).** Measured 2026-09-29: eight `ON DELETE CASCADE` foreign keys
   point at `bodha_msr_signals`, from `kala_convergence` and from `kala_darshana`, `kala_bhavishya`, `kala_activation`,
   `kala_obstruction`, `bodha_signal_embeddings`, `bodha_contradictions`. Suvarṇa's first rebuild wave contains two
   writers that delete signals, so it waits until F-3 removes the cascade on all eight keys and the change is applied.
7. **Saṅgam only.** Your unapplied migrations are 1088, 1089, 1090, 1092 and 1093; 1091 belongs to the Gochara lane and
   is applied.

**Please acknowledge** once you have read this, so Suvarṇa's launch item FI-8 can close:
```
python3 -m suvarna_tracker.emit note --actor l3-<family> --detail "ACK FI-8: correction notice v1.2 read; prompt v1.3"
```

If anything you have already done conflicts with these, tell the native; nothing here asks you to undo work.
