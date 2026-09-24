# Step 2 evidence — Restore drill

Runbook step 2 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Restore drill — 2026-08-23 dump into disposable DB, 38,287 v1 rows content-checked
- **Gate:** row-by-row digest equality; 2,667-uncovered-id report attached
- **Reversal:** none needed
- **DSN target:** n/a — NOT_RUN (no dump locally); would target a disposable DB
- **Operator / principal:** subagent (l3/gochara-autonomous-wp0-7, §7.B tranche 1)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->

## 2026-09-24 — NOT_RUN (no dump locally — carried, honest record)

Per the native's tranche-1 authorization message: "step 2 restore-drill = NOT_RUN
(no dump locally — record honestly)". Verified at run time: no 2026-08-23 logical
dump exists on this machine (`~/Downloads`, `/tmp` scanned; nothing matching
dump/backup/amjis). The script itself refuses to run without an explicit `--dump`
path (exit 3 by design).

Consequence carried to the tranche record: the v1 rollback corpus's digest
equality against the 2026-08-23 dump (38,287 rows, and the 2,667-uncovered-ids
gap report) is **unverified in this tranche**. The production v1 corpus itself is
now hard-protected by step 3's generation guard, but the restore-drill evidence
remains outstanding and must be produced before the step-8 flip can be considered
fully evidenced (or the native must rule it waivable).

**Verdict: step 2 NOT_RUN — recorded, not waived.**
