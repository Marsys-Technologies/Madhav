---
artifact: CLAUDECODE_BRIEF_PSHIP_S6H_v1_0.md
type: DEPLOY_RUNBOOK
version: 1.0
status: READY
authored_by: Cowork 2026-05-20
session_id: PSHIP-S6H
session_name: PSHIP-S6H — Merge + deploy + prod migration/bootstrap + verify (HUMAN runbook)
executor: NATIVE (human) — NOT a Conductor session
worktree:
  branch: feature/panchang-ship
predecessor: PSHIP-S5H (ship-readiness GO)
---

# PSHIP-S6H — Human Deploy Runbook
## Merge the hybrid Panchang ship, deploy web + sidecar, run migration 061 + bootstrap, verify

This is a HUMAN runbook, not an autonomous session. Run it after PSHIP-S5H emits a GO. The Conductor does not execute this — production merge + deploy + DB migration are human-gated by your own autonomy boundary (per-session commits autonomous; PR-to-main + deploy human).

---

## Step 0 — Confirm GO
Read `00_ARCHITECTURE/PSHIP_SHIP_READINESS_H_v1_0.md` on `feature/panchang-ship`. Confirm GO (not NO-GO). Note the bootstrap status (populated in S3H, or deferred to this step).

## Step 1 — Open the PR
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
gh pr create --base main --head feature/panchang-ship \
  --title "Panchang module (hybrid) — UI + Muhurat + iCal + Ask-Madhav + 5-col cache extension" \
  --body-file 00_ARCHITECTURE/PSHIP_PR_BODY_H.md
```
(If `gh` isn't set up: open the compare URL GitHub printed on the last push.)

## Step 2 — Review the PR yourself
Focus the review on:
- The shared-file integrations (nav, sidecar main.py, deploy.yml, CLAUDE.md §E) — do they sit cleanly on main's current versions?
- `query_panchanga.ts`: confirm ONLY main's SQL tool is in RETRIEVAL_TOOLS (D6) — our sidecar logic is a non-tool module.
- `PLANNER_PROMPT_v2_0.md`: R-PA extended with the 13 triggers; main's R-TC untouched; R-PCI added.
- Migration 061: 5 JSONB columns; matches main's migration conventions.

## Step 3 — Merge
Merge the PR to main (squash or merge-commit per your convention). Resolve any CLAUDE.md conflict by keeping ALL workstream entries (Conductor + Panchang + whatever main has).

## Step 4 — Apply migration 061 on production DB
```bash
# With the Cloud SQL Auth Proxy running (platform/scripts/start_db_proxy.sh, port 5433):
psql "$DATABASE_URL" -f platform/supabase/migrations/061_extend_panchanga_daily.sql
# Verify the 5 columns exist:
psql "$DATABASE_URL" -c "\d panchanga_daily" | grep -E "special_yogas|inauspicious|auspicious|choghadiya|hora"
```

## Step 5 — Run the bootstrap to populate the 5 new columns (~60 min, 73K rows)
If S3H deferred the population (check PSHIP_SHIP_READINESS_H): run the documented bootstrap command now against prod. If S3H populated a dev/staging DB, run it against prod here.
```bash
# Exact command is in PSHIP_SHIP_READINESS_H_v1_0.md (S3H documented it).
# Roughly:
cd platform/python-sidecar && python3 -m pipeline.bootstrap_panchanga --extend-columns --all-rows
# Verify a sample row now has the new columns populated:
psql "$DATABASE_URL" -c "SELECT date, special_yogas IS NOT NULL AS has_yogas, choghadiya IS NOT NULL AS has_chog FROM panchanga_daily LIMIT 5;"
```
**Until this runs, the SQL tool returns null for the new columns** — chat queries for special yogas / rahu kalam / choghadiya would come back empty even though routing works.

## Step 6 — Deploy web + sidecar
Trigger the deploy (merge to main usually triggers `.github/workflows/deploy.yml`). Confirm BOTH jobs run:
- `deploy-web` — the Next.js app (gets /panchang route + nav + planner prompt)
- `deploy-sidecar` — the Python sidecar (gets routers/panchang.py + muhurat.py for the UI's live path)
```bash
# Watch the deploy; confirm both jobs green. Note the new revision.
gh run watch   # or watch in GitHub Actions UI
```

## Step 7 — Verify production
- **UI path:** visit the production `/panchang` — confirm it renders live data (5 angas, timings, special yogas, choghadiya, hora, Muhurat Finder). This exercises the sidecar's panchang router + the auth fix (the prod sidecar enforces the API key — if /panchang 401s, the auth fix didn't deploy).
- **Planner path:** in production chat, ask "what's the rahu kalam today and is there a special yoga?" — confirm the answer comes back populated (proves R-PA routing + the 5-col cache + the bootstrap).
- **Regression:** ask a transit-context question (main's R-TC) — confirm it still behaves as before.

## Step 8 — Close-out
- Update `CURRENT_STATE` + `SESSION_LOG`: Panchang module SHIPPED to prod (revision X).
- Update `CLAUDE.md §E` Panchang entry → status reflects "live in prod."
- Retire the PanchangShip worktree if done: `git worktree remove /Users/Dev/Vibe-Coding/Apps/PanchangShip` (after confirming merged).
- The deferred Wave 3 EXTEND items (v2 muhurat finer windows, full 15+ event set, real acharya validation) remain for a future round.

---

## Rollback
If prod /panchang or chat panchang breaks post-deploy: `git revert` the merge commit + redeploy. The migration 061 columns are additive (nullable) — they don't break main's existing query_panchanga, so the DB doesn't need rollback. The risk surface is the planner prompt (R-PA extension) — if it mis-routes, revert is the fast path.

*End — PSHIP-S6H human deploy runbook.*
