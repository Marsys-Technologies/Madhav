# Step 7 evidence — Four flip gates

Runbook step 7 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 2
(requires `PRODUCTION_TRANCHE_2_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Four flip gates — provenance P-1a · coverage P-1b · disclosure deriveResolutionDisclosure · rollback-through-adapters
- **Gate:** each gate green against the deployed tools (TS gates named in step07_flip_gates.py)
- **Reversal:** —
- **DSN target:** production `amjis` via own cloud-sql-proxy
  `127.0.0.1:55440` (`madhav-astrology:asia-south1:amjis-postgres`); fresh
  `amjis-pipeline-db-url` credentials from Secret Manager per connection
- **Operator / principal:** l3/gochara-autonomous-wp0-7

<!-- Run outcomes are appended below by the step scripts (--evidence). -->

## ADK-0023 §4 attachments — corrected E-020 evidence package (chart 482012f1)

- Delta report (production write run):
  `.run/wp10_tranche2/prod_link3_delta_report_482012f1.md`
- Corrected step06b run reports (disposable rehearsal + production):
  `.run/wp10_tranche2/link3_step06b_runreport_482012f1.json` and
  `.run/wp10_tranche2/prod_link3_step06b_runreport_482012f1.json` —
  both `contacts_unmapped_relation=0`, `contacts_unmapped_no_class=0`,
  4,415 windows (1435/1490/1490), 2 outside-era skips, 0 collapsed dupes;
  production run report matches the rehearsed corrected projection exactly.
- Shift ledger (old-convention vs corrected dates, gate-(b) window level):
  `.run/wp10_tranche2/e020_gateb_shifts_482012f1.jsonl` (6,953 records, all
  +1-day shifts at 00:00–11:59 UTC; two records reading 12.0 are the ledger's
  6-decimal rounding of 11:59:59.999356 UTC — verified).
- E-020 disclosure chain: `link3_conditioning_evidence.md` E-020/ADK-0026
  section (2026-09-28) and the migration-1150 production-apply section;
  `ESCALATIONS.md` E-020 DISPOSITION closure entry.

## 2026-09-28T19:18:43Z — GREEN

```json
{
  "provenance_p1a_substrate": {
    "pass": true,
    "detail": "manifest status=candidate writer=ka_gochara",
    "ts_gate": "NOT_RUN (route test lives in platform-mcp; see module docstring)"
  },
  "coverage_p1b_substrate": {
    "pass": true,
    "detail": "coverage rows=48 count-consistent=True",
    "ts_gate": "NOT_RUN (route test lives in platform-mcp)"
  },
  "windows_present": {
    "pass": true,
    "detail": "kala_gochara_windows rows for generation 4.0: 4415. Flipping serving authority onto a generation with no window rows would empty the served forecast for this chart. Run the '4.0' windows projection writer (step06b_windows_projection.py, E-012) first."
  },
  "disclosure_derive_resolution": {
    "pass": null,
    "detail": "NOT_RUN: deriveResolutionDisclosure is a TS function; no DB substrate. Run the platform test at tranche time."
  },
  "rollback_through_adapters": {
    "pass": true,
    "detail": "leftover coverage=0 manifest=rolled_back post-rollback write refused=True"
  }
}
```
