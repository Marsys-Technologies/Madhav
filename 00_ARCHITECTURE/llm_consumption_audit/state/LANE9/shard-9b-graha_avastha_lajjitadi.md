# Shard 9b — graha_avastha_lajjitadi

**Shard id:** `9b-graha_avastha_lajjitadi`
**Charts:** Abhisek `482012f1`, Abhinandan `1c826d5a`

## Exact SQL run
9b 5-cell recipe with `f.fact_category = 'graha_avastha_lajjitadi'`; plus chart_facts COUNT.

## Verbatim results
- chart_facts rows: both 45.
- cell1: Abhisek 15, Abhinandan 29 → CONSUMED.
- cell2 salience: both `supporting` only (Abhisek `supporting=15`, Abhinandan `supporting=29`).
- cell3 attribution: Abhisek 15/15, Abhinandan 29/29 → 100%.
- cell4 domains: both `character|relationship` (UNIQUE within shard — only category not mapped to career).
- cell5 type: both `composite_state`.

## Five-cell verdicts
1. Consumed? YES.
2. Salience: ALL `supporting` — proportionate; no inflation. PASS.
3. Attribution: 100%. PASS.
4. Domain: `character|relationship` — sensibly differentiated (lajjitadi states — lajjita/garvita/kshudita/trushita/mudita/kshobhita — carry emotional/relational valence). PASS.
5. Emergence: 15–29 signals, all composite_state.

## design_correctness_verdict: SOUND
Best-calibrated category in the shard: proportionate supporting-tier salience, full attribution, and the ONLY category whose domain mapping is differentiated to `character|relationship` rather than the default `character|career`. This is the correct pattern the other 11 categories fail to follow.

## Findings
- **PASS evidence.** Consumed (cell1 15/29), fully attributed (cell3 15/15, 29/29), salience proportionate (cell2 `supporting` only), domain sensibly `character|relationship` (cell4). No defect.
- Note: contrast with `graha_avastha_lajjitadi_per_varga` which maps the SAME avastha type to `character|career` (domain inconsistency — logged in that shard).
