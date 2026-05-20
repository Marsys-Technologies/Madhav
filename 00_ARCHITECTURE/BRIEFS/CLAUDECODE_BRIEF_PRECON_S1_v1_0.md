---
artifact: CLAUDECODE_BRIEF_PRECON_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-20
session_id: PRECON-S1
session_name: PRECON-S1 — Panchang reconciliation analysis (READ-ONLY, produces spec)
executor: Claude Code (single session — NOT via Conductor; direct paste)
execution_mode: read-only investigation, --dangerously-skip-permissions
worktree:
  name: PanchangShip
  branch: feature/panchang-ship
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
compares: origin/main (ephemeris-campaign panchanga) vs origin/feature/phase-4c-panchang (our Conductor-built module)
output: 00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md (+ re-scoped ship plan)
hard_constraint: NO code changes. This session ONLY reads and writes the spec document.
---

# CLAUDECODE_BRIEF — PRECON-S1
## Panchang reconciliation analysis: main's tool-path vs our full module

Main already shipped a `query_panchanga` tool (5 limbs, precomputed `panchanga_daily` table, R-PA planner rule). We built a richer module (live engine + special yogas + /panchang UI + Muhurat Finder + iCal + Ask-Madhav) on `feature/phase-4c-panchang`, with its own colliding `query_panchanga` + repurposed R-TC rule. This session produces a precise reconciliation spec so we can re-scope the ship round correctly. **It changes NO code** — it reads both branches and writes one analysis document.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
git branch --show-current   # feature/panchang-ship
git fetch origin --quiet
git rev-parse --verify origin/main
git rev-parse --verify origin/feature/phase-4c-panchang
test -f 00_ARCHITECTURE/PSHIP_CONFLICT_MAP.md    # PSHIP-S1 output — useful input
test -f 00_ARCHITECTURE/PSHIP_FILE_INVENTORY.md
```

## §2 — Mandatory reads (read BOTH branch versions of each)
1. `CLAUDE.md` §C
2. This brief
3. `00_ARCHITECTURE/PSHIP_FILE_INVENTORY.md` + `PSHIP_CONFLICT_MAP.md` (the 132 additive / 22 shared classification from PSHIP-S1)
4. `query_panchanga.ts` — BOTH: `git show origin/main:platform/src/lib/retrieve/query_panchanga.ts` and `git show origin/feature/phase-4c-panchang:platform/src/lib/retrieve/query_panchanga.ts`
5. `query_panchanga.test.ts` — both branch versions
6. Main's compute path: `git show origin/main:platform/python-sidecar/pipeline/bootstrap_panchanga.py` + `panchanga_derivations.py`; find the `panchanga_daily` table migration (`git ls-tree -r origin/main -- platform/supabase/migrations/ | grep -i panchang` or grep migrations for panchanga_daily)
7. Our compute path: `git show origin/feature/phase-4c-panchang:platform/python-sidecar/panchang_engine/__init__.py` + `special_yogas.py` + `muhurat.py` + `routers/panchang.py`
8. Planner rules — both: main's R-PA (`git show origin/main:00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`, the R-PA. PANCHANGA ANCHOR block) and ours (the R-TC repurposed block on feature/phase-4c-panchang)

## §3 — Scope (8 analysis items → one spec document)

Produce `00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md` answering each:

### Item 1 — query_panchanga tool diff
Side-by-side: params accepted, return shape, fields surfaced. Does main return only the 5 limbs? Does ours return 5 limbs + special_yogas + timings + planets? Are the interfaces compatible or divergent? Which is a superset of which? Document the exact field delta.

**AC.PRECON1.1:** Tool-diff table in spec — every field of each, marked shared / main-only / ours-only.

### Item 2 — Compute-path diff
Main: precomputed `panchanga_daily` table via pipeline derivations (batch). Ours: live `panchang_engine` via `/api/compute/panchanga` (on-demand). Document: what main's precompute covers (does it include special yogas? muhurta? sunrise-anchoring? what date range is seeded?), how it's refreshed, vs what our engine computes live. Crucially: **is main's `panchanga_daily` the cache we deferred as 4C-2?** If so, note that main already solved caching.

**AC.PRECON1.2:** Compute-path comparison in spec, including whether main's precompute already covers our special-yogas/muhurta needs or not.

### Item 3 — Planner routing diff
Main's R-PA (Panchanga Anchor) vs our repurposed R-TC. Do they trigger on the same query phrases? Does R-PA already cover muhurta/auspicious-day queries (it appears to, per line 740-742 "good day for marriage")? What routing, if any, does ours add that R-PA lacks (special-yoga queries? Muhurat Finder?)? Is R-PA sufficient as-is, or does it need extension?

**AC.PRECON1.3:** Routing-diff in spec — R-PA coverage vs our rule, with the delta of triggers each handles.

### Item 4 — Net-new inventory (no main equivalent)
Catalog everything in our module that main has NO version of: /panchang UI page + all components, Muhurat Finder (modal + scoring + weights), iCal export + signed feed, Ask-Madhav context injection, special_yogas detection, the muhurat scoring engine. These are pure-additive (ship cleanly regardless of the tool reconciliation).

**AC.PRECON1.4:** Net-new inventory in spec — each item confirmed absent on main.

### Item 5 — True-collision inventory
Catalog what genuinely collides (both branches define it differently): `query_panchanga.ts`, the planner rule slot, possibly `routers/panchang.py` vs main's pipeline approach, the `panchanga_daily` vs `panchang_daily` table naming (note: main uses `panchanga_daily`, our deferred 4C-2 spec'd `panchang_daily` — even the table names differ).

**AC.PRECON1.5:** Collision inventory in spec — each with main's version vs ours and why they conflict.

### Item 6 — Reconciliation recommendation
Based on Items 1–5, recommend the integration architecture. Evaluate honestly:
- **Option L (layer):** keep main's query_panchanga + R-PA + panchanga_daily cache as the query path; add only our net-new layer (UI, Muhurat, iCal, Ask-Madhav, special yogas), rewiring our UI to consume main's tool/table; add our engine ONLY for what main's precompute lacks (likely special yogas + muhurta scoring).
- **Option R (replace):** our module supersedes main's tool + cache.
- **Option H (hybrid):** main's precomputed-table tool path + our special-yogas/muhurta extensions to the precompute + our UI layer.
Give a clear recommendation with rationale, accounting for: main's cache is the 4C-2 we deferred (keeping it is a win), the duplicate-tool maintenance cost, and the effort delta.

**AC.PRECON1.6:** Recommendation in spec with rationale + the rejected options' trade-offs.

### Item 7 — Re-scoped ship session plan
Given the recommended option, define the NEW ship sessions (replacing PSHIP-S1–S4). For each: one-line scope, what it touches, its gate. Estimate count + which are autonomous vs human (merge/deploy stay human).

**AC.PRECON1.7:** Re-scoped ship plan in spec — session list with scope + gates.

### Item 8 — Disposition of PSHIP-S1's work
PSHIP-S1 transplanted 132 additive files + wrote the conflict map. State which of those transplanted files survive under the recommended option (the net-new ones do; the colliding query_panchanga likely gets dropped in favor of main's), and what the re-scoped round reuses vs discards.

**AC.PRECON1.8:** PSHIP-S1 disposition noted in spec.

---

## §4 — Hard constraint: READ-ONLY
This session changes NO application code, NO planner prompt, NO manifest. It reads both branches (via `git show`) and writes exactly ONE new file: `00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md` (+ governance state at close). If you find yourself editing a `.ts`/`.py`/prompt file, STOP — that's the re-scoped ship round's job, not this analysis.

## §5 — Constraints
**may_touch:** `00_ARCHITECTURE/PANCHANG_RECONCILIATION_SPEC_v1_0.md` (new); CURRENT_STATE + SESSION_LOG at close; this brief.
**must_not_touch:** ALL application code, planner prompt, manifest, the transplanted files, the Conductor files, both branches' code (read-only via git show), corpus.

## §6 — Close checklist
- [ ] All 8 analysis items in the spec
- [ ] Clear reconciliation recommendation (L / R / H) with rationale
- [ ] Re-scoped ship session plan
- [ ] PSHIP-S1 disposition documented
- [ ] ZERO code changes (only the spec file written)
- [ ] CURRENT_STATE + SESSION_LOG updated; FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Main's panchanga = ephemeris-campaign Phase 4C: query_panchanga (5 limbs) + panchanga_daily precomputed table + R-PA planner rule. Tested, on main.
- Ours = Conductor-built: query_panchanga (5 limbs + special yogas, live engine) + panchang_engine + /panchang UI + Muhurat Finder + iCal + Ask-Madhav + repurposed R-TC. On feature/phase-4c-panchang, unmerged.
- Table name mismatch: main `panchanga_daily` vs our deferred-4C-2 `panchang_daily`.
- main's precomputed table IS likely the cache we deferred — keeping it may be the win.
- The reconciliation decision determines the re-scoped ship round. NO shipping until this spec is reviewed by native.

## §9 — Canary
The recommendation (Item 6) must be grounded in the actual diffs (Items 1–5), not asserted. If the spec recommends an option without the field-level / routing-level evidence to back it, it's incomplete — the whole point is to decide on facts this time, not inference.

*End — PRECON-S1. Read-only reconciliation analysis. Re-scoped ship round follows native review of the spec.*
