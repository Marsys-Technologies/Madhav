---
artifact: L3_FAMILY_CORRECTION_NOTICE
version: "1.0"
status: READY — paste into each L3 family session (Gochara, Saṅgam, Kṣetra)
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa" (plan item FI-8)
changelog:
  - "1.0 (2026-09-29): corrections found by Suvarṇa review pass 1, relayed as a report."
---

# Corrections to your start prompt (a report from Strategic Suvarṇa, not a new instruction)

Your prompt has been corrected to v1.1. Please re-read it:
`/Users/Dev/madhav-suvarna-plan/00_ARCHITECTURE/briefs/suvarna/prompts/L3_<GOCHARA|SANGAM|KSHETRA>_FINAL_BRIEF_PROMPT_v1_0.md`

What changed:

1. **The census command in v1.0 does not run.** `--out` must be a file (not a folder), and the read-only credential must be sourced. Use, from any folder:
   ```
   mkdir -p <evidence folder>
   export PYTHONPATH=/Users/Dev/madhav-suvarna-plan/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna
   python3 -m suvarna_tracker.census_lock --wait 900 --emit --actor l3-<family> -- \
     bash -c 'source ~/.config/suvarna/pgenv.sh && cd /Users/Dev/madhav-nikasha && python3 platform/scripts/governance/asset_census.py --layer L3 --out <evidence folder>/census_L3.json'
   ```
   The lock makes sure only one census runs at a time across all sessions (exit 75 = another census is running; wait and retry).
2. **Certification (native decision D2).** Your assets are certified by Suvarṇa's independent re-measure, and only if they were built by an **orchestrator run**, never by a hand-run cutover script. For Gochara: no certification until the registered writer produces the new generation.
3. **Rulings.** When the native seals one of your family's rulings (F-1…F-6), Strategic Suvarṇa records it as `decided` in the authoritative decisions log. Your session emits `requested` only, never `decided`.
4. **Template revision.** Write in your brief's frontmatter which revision of the tier-4 template it follows. The template is re-sealed at the engine freeze, and Suvarṇa maps briefs to the new revision afterwards.
5. **Saṅgam only.** Your unapplied migrations are 1088, 1089, 1090, 1092 and 1093; 1091 belongs to the Gochara lane and is applied.

If anything you have already done conflicts with these, tell the native; nothing here asks you to undo work.
