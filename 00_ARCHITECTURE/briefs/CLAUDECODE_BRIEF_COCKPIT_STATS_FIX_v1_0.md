# Cockpit Stats Fix — 3 live bugs the stats endpoint exposed (paste into Claude Code / Antigravity)

**Context:** Chrome-MCP inspection of `/api/cockpit/registry` + `/api/cockpit/stats?chartId=482012f1` on
localhost (main @ 440a236b) found the cockpit is NOT green despite the L0+L1 "cockpit green" seals. The seals'
prod-verify ran count SQL BY HAND (param bound) and never hit the stats endpoint (param not bound) — so these
survived. **The endpoint is the ground truth; fix to make it clean.** Standards: surgical migrations only (≥ 311,
ledger-reconciled); seed-consistency; inspect-the-SQL-site not metadata ([[feedback-sql-param-binding-inspect-site]]);
only `482012f1`; verify via the ENDPOINT after, not hand-SQL.

**Exact API evidence (do not re-derive — this is what the endpoint returns now):**
- `bg_reference`: target_floor=**null**, rows 1485, state lit, **build_state_stale=true**, last_built_at=**null**
- `bg_ontology`: target_floor=**null**, rows 623, state lit, **stale=true**, last_built_at=**null**
- `bg_nakshatra`: target_floor=**null**, rows 2857, state lit, **stale=true**, last_built_at=**null**
- ALL `ga_*` (ga_condition, ga_dashas, ga_medical, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati,
  ga_structural, ga_strength, ga_sensitive, ga_vargas, ga_tajaka, ga_yoga, ga_vastu, ga_transit_anchors, …):
  state=**error**, rows=null, **error="there is no parameter $1"**

---

## BUG 3 (FIX FIRST — highest impact): L1 ga_* count_sql "there is no parameter $1"

**Root cause:** migrations 309/310 rewrote L1 count_sqls to chart-scoped `WHERE chart_id = $1`. The cockpit stats
route executes the stored count_sql but does NOT bind `$1` for these assets → Postgres throws "there is no
parameter $1". This is the EXACT recurrence of the known param-binding bug: the route decides whether to bind
`$1` from a sibling metadata field (likely `scope === 'per_chart'` or similar) instead of from whether the SQL
literally contains `$1`.

**Fix — at the SQL site, not metadata:** in the cockpit stats route (`/api/cockpit/stats` handler — find where it
executes `asset.count_sql`), bind `$1 = chartId` whenever the count_sql text contains `$1` (e.g.
`const params = /\$1/.test(sql) ? [chartId] : []`), regardless of any scope/metadata flag. This is the
closed-Round-3.6 pattern ([[feedback-sql-param-binding-inspect-site]]) — re-opened by the new count_sqls.
- Verify: after the fix, EVERY `ga_*` asset in `/api/cockpit/stats?chartId=482012f1` returns `state=lit`,
  non-null `actual_rows`, `error=null`. Spot-check ga_structural≈74,034, ga_strength≈11,936, ga_sensitive≈8,610,
  ga_condition≈2,880, ga_sade_sati≈11,019.
- This is a CODE fix (route handler), not a migration. Add/extend a test that asserts the stats route binds `$1`
  whenever count_sql contains it (gate on the SQL, not metadata) so it can't regress again.

---

## BUG 1: L0 three assets with NULL target_floor → empty progress bar

`bg_reference`, `bg_ontology`, `bg_nakshatra` have `target_floor=null` → the bar has no denominator → renders
bare count + empty bar. (The earlier L0 floor touch-up never reached these; bg_nakshatra was never briefed.)
Migration 311:
```sql
UPDATE asset_registry SET target_floor = 1485 WHERE asset_id='bg_reference';
UPDATE asset_registry SET target_floor = 623  WHERE asset_id='bg_ontology';
UPDATE asset_registry SET target_floor = 2857 WHERE asset_id='bg_nakshatra';
```
Patch the same three floors in `asset_registry_seed.ts`. (Sealed L0 — disclosed floor micro-fix, native aware.)
Verify the floor values match the achieved counts FIRST (run each asset's count_sql with the binding fix; set
floor = achieved). If any count differs from the rows shown above, use the measured count, not the number here.

---

## BUG 2: L0 three assets build_state_stale (last_built_at = null)

Same `bg_reference` / `bg_ontology` / `bg_nakshatra`: state=lit but `last_built_at=null` → cockpit flags stale.
Re-stamp their `asset_throughput` last_built_at (a targeted throughput write, OR re-run their builds via the
orchestrator so the throughput update lands). After: `build_state_stale=false`, `last_built_at` non-null in the
stats endpoint. (Note: these are global L0 assets — confirm the throughput write uses the global/NULL-chart key,
the `IS NOT DISTINCT FROM` pattern, not `= %s`.)

---

## VERIFY — via the ENDPOINT, not hand-SQL (the lesson)

After all three fixes, hit the actual cockpit data path:
1. `GET /api/cockpit/registry` → bg_reference/bg_ontology/bg_nakshatra now have non-null target_floor.
2. `GET /api/cockpit/stats?chartId=482012f1` → EVERY asset (L0 + L1): `state=lit`, non-null `actual_rows`,
   `error=null`, `build_state_stale=false`, non-null `last_built_at`. ZERO assets with state=error.
3. Load `/clients/482012f1/nirmana`, expand Brahma Jñāna + Gaṇita: all bars filled (`count / target`), no empty
   bars, no "build-state stale", no red. Screenshot to confirm.
4. CI green; merge-verify; migration 311 ledger-reconciled on prod.

**Process rail (record it):** "cockpit green" in any future seal MUST be verified by hitting
`/api/cockpit/stats?chartId=...` and asserting every asset returns lit/non-null/no-error — NOT by running the
count SQL by hand with the param bound. The two fail differently; only the endpoint is the truth the user sees.

Report back: the stats-endpoint JSON (all assets lit, zero errors), the 3 floors set, and the screenshot.
