# shard-9b-graha_dispositor_chain

**Shard id:** graha_dispositor_chain (Lane 9b)
**Charts:** 482=Abhisek, 1c826=Abhinandan

## Exact SQL run
chart_facts: 482=45, 1c826=45. 5-cell recipe (standard 9b CTE).

## Verbatim results
- cell1: 482=45, 1c826=45
- cell2: 482=`chart_defining=5, major=30, supporting=10`; 1c826=`background=10, chart_defining=5, major=24, supporting=6`
- cell3: 482=`45/45`, 1c826=`45/45`
- cell4: both=`character|career`
- cell5: both=`composite_state=45`

## 5-cell verdicts
1. Consumed? YES (45/45 = 9 grahas × 5, one per chain per graha).
2. Salience: reasonable spread (5 chart_defining).
3. Attribution: 100%. AFFIRMATIVE PASS.
4. Domain: mono-mapped `character|career` — a dispositor terminating in the 7th/2nd/6th implicates relationship/wealth/health, collapsed to default.
5. Type: **composite_state** — the dispositor chain (an inherently multi-hop structure: sign→nakshatra→navamsha→terminus) is flattened into a flat composite_state signal, NOT a distinct multi-hop/chain signal class. Confirms G-6 (no multi-hop chain signal class in MSR) from the ingestion side.

## design_correctness_verdict: WEAK
Consumed + fully attributed, but the multi-hop chain semantics are lost (flattened to composite_state, G-6) and domain is default-collapsed to character|career, so a wealth/relationship query cannot leverage where a graha's dispositor chain terminates.

## Findings
- **F1** class 6 (UNUSABLE FORM) / G-6 corroboration — severity MED. dispositor_chain ingested as `signal_type_class=composite_state` (cell5 both = `composite_state=45`); no chain/multi-hop class exists, so the terminus-of-chain relationship is not queryable as a chain. Independent 9b-side confirmation of G-6.
- **F2** class 2 (WRONG) — severity MED. Domain invariant `character|career` (cell4) irrespective of chain terminus house.
