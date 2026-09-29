# Step 8 evidence — Flip

Runbook step 8 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 2
(requires `PRODUCTION_TRANCHE_2_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Flip — authoritative_generation='4.0', evidence_ref=manifest_id, manifest published
- **Gate:** walkthroughs §3 F-02 re-run green (ordinary quarter; marriage 2013)
- **Reversal:** re-point to '3.0'; manifest rolled_back (Kṣetra-edge consequence disclosed)
- **DSN target:** production `amjis` via own cloud-sql-proxy
  `127.0.0.1:55440` (`madhav-astrology:asia-south1:amjis-postgres`); fresh
  `amjis-pipeline-db-url` credentials from Secret Manager per connection
- **Operator / principal:** l3/gochara-autonomous-wp0-7

<!-- Run outcomes are appended below by the step scripts (--evidence). -->

## 2026-09-28T19:22:58Z — GREEN

{
  "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
  "generation": "4.0",
  "action": "flipped",
  "manifest_id": "d54d899b-7923-4b0d-92c5-0ff499f4a0bf",
  "evidence_ref": "d54d899b-7923-4b0d-92c5-0ff499f4a0bf",
  "contacts": 138837,
  "flipped_by": "l3/gochara-autonomous-wp0-7"
}

## Flip gate notes (2026-09-28T19:25Z)

- **Conjunct-(i) vacuity NOTE (required by ADK-0024 §4):** migration 1091's
  conjunct (i) checks `active_sentences` elements for a `contact_id` KEY;
  step06b stores bare contact-id strings, so (i) passes VACUOUSLY for '4.0'
  rows — "integrity green" is not earned on sentence-reference integrity by
  an empty check.
- **F-02 walkthrough re-run (step-8 gate, run under soak evaluation #1 — see
  step09_evidence.md for the full record):** ordinary quarter 2027-03→05 →
  137 '4.0' rows, all with contacts (44 day / 49 era / 44 month); marriage
  touching 2013 → 0 rows, outside the manifest's disclosed horizon
  [2020-01-01, 2030-01-01) — absence by design, not a contactless-episode
  defect; marriage in-horizon → 152 rows, 152 with contacts.
- **Write-path note (three failed attempts before the successful write):**
  step06b holds one connection+transaction across its ~25-min client-side
  compute phase. Attempt 1 died to the server's
  `idle_in_transaction_session_timeout=600000`; attempts 2–3 to TCP
  ETIMEDOUT on the proxy↔instance path (transient — a 40-min keepalive probe
  with the same session parameters then ran clean, disproving a hard
  connection cap). The successful attempt 4 used session-only conninfo
  parameters (`options=-c idle_in_transaction_session_timeout=3600000`,
  `keepalives=1/30/10/5`); no server-side setting was changed, and each
  failed attempt rolled back cleanly (zero '4.0' rows, manifest still
  candidate — verified after each).

## 2026-09-28T19:29:44Z — REVERSED

{
  "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
  "generation": "4.0",
  "action": "reversed",
  "authority": "3.0",
  "manifest_id": "d54d899b-7923-4b0d-92c5-0ff499f4a0bf",
  "manifest_status": "rolled_back",
  "windows_deleted": 4415,
  "label_burned": "a rolled_back manifest refuses re-publication \u2014 a re-attempt builds under a NEW generation label"
}
