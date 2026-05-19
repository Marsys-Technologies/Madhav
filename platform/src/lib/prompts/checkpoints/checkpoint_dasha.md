# Checkpoint Dasha — Remediation Prompt

This block is appended to the synthesis prompt when `checkpoint_dasha` detects a DASHA DISCIPLINE GATE violation in the previous synthesis attempt.

---

DASHA REMEDIATION (your previous response violated the DASHA DISCIPLINE GATE):

Violations detected:
{{violation_list}}

Canonical dasha schedule from chart_facts (use these EXACT citations):
{{canonical_dasha_snippet}}

Regenerate the response with corrected dasha claims, citing DSH.V.NNN exactly as shown above. Do not extrapolate from generic Vimshottari knowledge — the chart_facts rows above are the ground truth.

Rules for corrected dasha claims:
1. Every temporal dasha claim ("current MD", "next MD", "upcoming AD") MUST be followed immediately by a (→ DSH.V.NNN, YYYY-MM-DD to YYYY-MM-DD) citation using the exact fact_id from the table above.
2. Do NOT invent date ranges. Use only dates from the chart_facts rows above.
3. Do NOT use Vimshottari sequence knowledge (e.g., "Saturn MD follows Mercury MD by default") as a substitute for the canonical table. The table is the only authority.
4. If the query_dasha_periods tool was called and returned rows, cite those rows. If it was not called, cite from the snippet above.
5. Generic historical mentions ("Saturn MD was a period of…") are acceptable without citation only when no temporal qualifier is present.
