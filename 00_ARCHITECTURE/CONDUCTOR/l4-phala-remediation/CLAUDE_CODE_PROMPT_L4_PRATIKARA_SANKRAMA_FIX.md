---
artifact: CLAUDE_CODE_PROMPT_L4_PRATIKARA_SANKRAMA_FIX.md
canonical_id: CLAUDE_CODE_PROMPT_L4_PRATIKARA_SANKRAMA_FIX
version: 1.0
status: READY — paste-prompt for Claude Code in Antigravity. Fix ph_pratikara (re-model on kala_obstruction) + rebuild ph_sankrama. NO SEAL.
authored_by: Cowork 2026-06-22
native_decision: "Fix ph_pratikara NOW — re-model mitigation on kala_obstruction's real columns. Then rebuild both so all 9 ph_* carry real rows before seal."
---

# Claude Code Prompt — ph_pratikara re-model + ph_sankrama rebuild (NO SEAL)

> Paste §PROMPT to Claude Code in Antigravity. Closes the two 0-row L4 assets so all 9 carry real rows.
> **DO NOT SEAL** — report back; the native holds the seal.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav, main, deployed revision
amjis-web-00671-sz6 / de9cb3f7). L4 Phala is live in prod with 7 of 9 ph_* assets lit-with-rows. Two are
lit-with-0-rows and are genuine writer defects. Fix both so all 9 carry real rows. **DO NOT seal** (no
DRAFT→CURRENT, no L4_PHALA_CLOSE, no CURRENT_STATE flip). Report back.

**RAILS:** Frozen contract (`@register`/WriterBase/`run(ctx)`; never commit/close `ctx.db_conn`; never
write asset_throughput; `WriterResult(rows_inserted=)`; `$1` count_sql; delete-then-insert). Anti-drift:
ph_pratikara writes ONLY `phala_mitigation`; ph_sankrama writes ONLY `phala_sankrama`. L-is-authority:
reference L3 ids, never restate values. N4 boundary. Canonical chart 482012f1 never mutated. Gemini/DeepSeek
only (Anthropic banned). Verify against the LIVE deployed revision, not the branch.

---

### FIX 1 — ph_pratikara: re-model mitigation on the REAL kala_obstruction schema
**Root cause (confirmed):** `writers/ph_pratikara.py::_load_obstructions` queries a table `ka_vighnakara`
that NEVER existed, selecting columns `afflicting_graha, obstruction_type, obstruction_start,
obstruction_end`. The SAVEPOINT/ROLLBACK catches the UndefinedTable, logs DEBUG, returns [] → silent 0
rows. The real L3 table is **`kala_obstruction`** (60 rows for the native), built by migration
`245_l3_ka_vighnakara.sql`, with these ACTUAL columns:
```
id BIGSERIAL, chart_id UUID, convergence_id BIGINT→kala_convergence(convergence_id),
signal_id UUID→bodha_msr_signals(signal_id),
obstruction_type TEXT (enum: malefic_transit | dasha_lord_afflicted | panchanga_obstruction |
                       rashi_dristi_conflict | combustion | gandanta | papakartari),
severity TEXT (mild|moderate|severe), severity_score DOUBLE (0..1), override_score DOUBLE (0..1),
obstruction_detail JSONB, source_citation TEXT, computed_at TIMESTAMPTZ
```
There is **no afflicting_graha and no start/end date column.** Those must be BRIDGED:
- **afflicting graha + window:** join `kala_obstruction.convergence_id → kala_convergence` and read the
  graha/lord + the window (peak/start/end) columns there; AND/OR extract from `obstruction_detail` JSONB
  (inspect its actual keys first: `SELECT obstruction_detail FROM kala_obstruction WHERE chart_id=... LIMIT 5`).
  Use whichever genuinely carries the graha + window. If neither does, the graha may be UNAVAILABLE for some
  obstructions — handle that honestly (null graha → fall back to a severity-keyed remedy program, see below).

**The re-model (writer-only; do NOT alter kala_obstruction or any L3 asset):**
1. `_load_obstructions`: `SELECT id, convergence_id, signal_id, obstruction_type, severity,
   severity_score, override_score, obstruction_detail FROM kala_obstruction WHERE chart_id = %s ORDER BY
   severity_score DESC`. (Order by severity_score so the worst obstructions get mitigation first.)
2. Bridge each obstruction to (afflicting_graha, window_start, window_end) via the convergence join /
   obstruction_detail per above.
3. The `run()` loop currently reads `obs['afflicting_graha']` / `obstruction_type` (as severity!) /
   `obstruction_start/end`. Rewrite it: severity ← `obs['severity']` (map mild/moderate/severe →
   intensity_tier light/moderate/intensive for P4 proportionality); afflicting_graha ← bridged value;
   window ← bridged dates. Keep the bo_upaya remedy assembly, but if the graha is null, key the program off
   `obstruction_type` (e.g. combustion/gandanta → general propitiation) instead of by-graha — don't drop the row.
4. `phala_mitigation` columns are unchanged (afflicting_graha, obstruction_severity, window_start/end,
   program_jsonb, etc. — see migration). Fill obstruction_severity from `severity`; carry severity_score +
   override_score into the program/proportionality basis so the mitigation is proportional (P4).
5. Update `services/ph_pratikara/engine.py::derive_mitigation_record` + MitigationContext to the new fields.
6. **REMOVE the silent-fail mask:** `_load_obstructions` should NOT swallow a missing-table exception into
   []. `kala_obstruction` exists now; if the query errors, it must FAIL LOUD (this silent catch is what hid
   the bug — same class as the ph_phaladesa stub + the Capricorn ascendant). Keep graceful [] ONLY for a
   genuinely-empty table, not for a query/column error.
7. Update `writers/ph_pratikara.py` docstring ("Reads: kala_obstruction · kala_convergence (bridge) ·
   phala_anchors · bodha_rm_remedy_prescriptions").
8. **Add a test** that would have caught this: assert ph_pratikara produces > 0 rows for the native given
   the 60 kala_obstruction rows, and that the column mapping matches kala_obstruction's real schema (guard
   against a future table/column drift). Run it.

### FIX 2 — ph_sankrama: rebuild (fix already committed)
`writers/ph_sankrama.py::_load_anchors` had `LIMIT 100`; with `ORDER BY confidence_high DESC NULLS LAST`
the top 100 were all `transition`-domain anchors, which have 0 `bodha_cdlm_cells` (domain_row='transition'
→ 0) → all joins nulled → 0 rows. The LIMIT was removed (commit 406d650e, deployed de9cb3f7). It just needs
a rebuild. **WATCH:** post-fix anchors are 5,365 CDLM-matched but **96% career (5,175)** / health 120 /
relationship 70 / transition+spiritual 0. Confirm the resulting phala_sankrama isn't pathologically
career-lopsided in a way that distorts the spillover graph — if it is, flag it (don't silently ship a skew).

### REBUILD both writers (deploy does NOT auto-rebuild)
Run the orchestrator click-Build path for the native (or the CLI equivalent) for the two assets:
```
cd platform/python-sidecar && PYTHONPATH=. python -m pipeline.orchestrator.run \
   --chart-id 482012f1-710e-4a25-994a-93821f5871aa --asset ph_pratikara --asset ph_sankrama
```
(or trigger via the cockpit Build for the Phala layer). Confirm both now write > 0 rows.

### VERIFY (against the live data)
```
# all 9 ph_ with rows>0 and lit
psql "$PROD_VIA_PROXY" -c "SELECT asset_id, rows_written, state FROM asset_throughput
  WHERE asset_id LIKE 'ph_%' ORDER BY asset_id;"
# ph_pratikara > 0 (≈ up to 60, one per obstruction × matched anchors); ph_sankrama > 0
```
Also: ph_pratikara rows reference real kala_obstruction ids (anti-drift ledger resolves); canonical chart
UNCHANGED; no L3 table mutated. CI green (no net-new failures); commit + push (auto-deploys — confirm the
new revision + that prod still shows all 9, now all with rows).

### REPORT — NO SEAL
Do NOT promote DRAFT→CURRENT, author L4_PHALA_CLOSE, set target_floors, or flip CURRENT_STATE. Report:
- ph_pratikara: the bridge used (convergence join vs obstruction_detail), final row count, the new test,
  any obstructions with null graha + how handled.
- ph_sankrama: rebuild row count + the career-skew check result.
- The post-rebuild `asset_throughput` table for all 9 ph_; the new prod revision SHA; any net-new CI.
- Anything needing the native. Then STOP.

---
*End. Re-model ph_pratikara on kala_obstruction's real columns (bridge graha/window via kala_convergence /
obstruction_detail; remove the silent-fail mask; add a guard test) + rebuild ph_sankrama. All 9 ph_ carry
real rows. NO SEAL.*
