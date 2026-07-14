---
artifact: BRIEF_D1_5A
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN)
wave: D-1.5a — gate-green judgment-substrate rework
version: 1.0
status: FROZEN+BOUND — all slots pre-bound by the 2026-07-14 Fable audit (file:line roots verified
  same-day); Binder at wave open ONLY re-verifies the §B bindings still hold (10-minute probe),
  since the estate is known to change between sessions.
governing: CONDUCTOR_PROTOCOL.md + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §3
gate: register §K.2 (12 assertions) + A5 two-chart assertion + final proof (wealth verdict moves
  off convergent_moderate/1.15 AND bearing_yogas carries the Dhana Yoga) — ALL as MCP calls on the
  DEPLOYED connector post-rebuild.
blocks: D-1.5b (does not start until this gate is green)
---

# D-1.5a — Gate-Green Rework

## FROZEN §F1 — Lane map (4 implementer lanes + Lane 0; all parallel except noted)

### Lane A-0 — Assertion harness + process (no product code)
- Build the executable assertion harness: every §K.2 assertion + Gate-B assertions (from the plan)
  as scripts that call the MCP surface and exit green/red. Verifiers and the gate runner run THIS,
  never prose. Acceptance: harness runs against today's deployed estate and correctly reports the
  CANONICAL BASELINE — reds #1–#5, #7–#9, #11; greens #10, #12; #6 split (green on
  `ganita_yoga_firings_get` non-empty, red on `ganita_yogas_get.yoga_fires` = 0). This baseline
  list is the single source of truth; §B B-2 re-verifies the same list.
- A6 process items: SESSION_LOG entries for Night-1 (retroactive) + this wave; DR-2 entry in
  DISAGREEMENT_REGISTER with delegation+ratification provenance; CURRENT_STATE §2 refresh (stale
  M6 banner → doctrine-waves campaign pointer); migration-directory ruling: **all future migrations
  in `platform/migrations/` only**, recorded in ONGOING_HYGIENE; lane-brief template note (CR-96/R-5).

### Lane A-α — Valence engine (Python; A1 then A2 sequentially inside this lane)
- **A1 (CR-90/DR-1):** reorder `compute_valence` (`ga_writers/ga_vichara_writer.py:269-322`) to
  honor `_PRECEDENCE` (`:83`) — trikoṇa evaluated before dusthāna; `strong_malefic` reserved for
  actors with NO trikoṇa ownership. Use `classify_actor`'s `primary` (already precedence-correct)
  instead of re-branching on the raw class set. Unit: `{trikona_lord, dusthana_lord}` actor →
  wealth-house target → benefic.
- **A2 (CR-91):** ingest `aspect_parashari` facts into `VicharaFactIndex` (`:186-228`) so
  graha-aspect signals get functional-lordship valence (dusthāna-lord aspects on H1/H2/H11 first);
  in `bo_laksana._resolve_valence` (`pipeline/orchestrator/writers/bo_laksana.py:300-344`) retire
  `keyword_heuristic_v1` for lord-link AND graha-aspect populations once vichara covers them
  (heuristic remains only for populations vichara genuinely doesn't judge — tagged, enumerated in
  the lane report); reconcile the stale "Lane 2 never landed" comments (`:863-872, 895-900, 960-965`).
- may_touch: `platform/python-sidecar/ga_writers/ga_vichara_writer.py`,
  `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py`, their tests.

### Lane A-β — Serving wiring + narrator/honesty (TypeScript)
- **A3 (CR-92 residue, R-3):** `judgment_query.bearing_yogas` reads `ga_yoga_firings`
  (firings-authoritative; MSR yoga signals demoted to a `corroboration` annotation) —
  `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:505-529`; verdict consumes
  detector strength + bhaṅga state (a fired Dhana Yoga must move the composite — if the verdict
  formula needs a yoga term, add it here); `ganita_yogas_get` serves firings (or a first-class
  pointer + counts) — `get_yoga_dosha.ts`; **same commit**: replace the stale "will never fire"
  description (`register_p1_ganita.ts:633-637`) with the true contract naming `ganita_yoga_firings_get`.
- **A4 (CR-93/94):** root-cause on the DEPLOYED path: (i) the PMP narrator's position fetch returns
  empty live → falls back to absence-in-page claims (denies Śaśa) — fix the fetch, and make the
  narrator's fallback honest ("positions unavailable — cannot rule") instead of asserting "not
  formed"; (ii) `coverage.served: 0` + `zero_rows_returned` on a 32-row page — wire to the actually
  served row count. Suspect the v3 envelope path counts a different variable than it serves.
- **B9-preview (1-line guard, in scope here because A-β owns these files):** `ganita_yogas_get`
  default page must not present `catalog_only`/`requires_pass` stub rows as findings (they may
  serve, but flagged; full gating lands in D-1.5b).
- may_touch: `platform/src/lib/retrieval/registry/layers/L1_ganita/*`,
  `register_d9_judgment.ts`, `register_p1_ganita.ts`, `platform-mcp/src/tools/*` (descriptions), tests.

### Lane A-γ — Correctness guards (Python; disjoint from A-α files)
- **A5 (CR-87 verification):** parametrized two-chart regression test — Abhinandan (1c826d5a)
  tara-bala/sade-sati/panchanga currents MUST differ from Abhisek (482012f1) given their different
  janma-nakshatra/Moon-sign/location; plus one live MCP comparison in the harness.
- **A7 (`_graha_aspects_house` off-by-one):** opposition/7th-house aspects return 0.0 instead of
  1.0 (`ga_writers/ga_structural_writer.py`) — Lane-1-flagged, pre-existing; consumed by
  `effective_dignity` v2 and A2's aspect valence. Fix + regression test + one live spot-check.
- may_touch: `ga_structural_writer.py`, `tests/` (ka_sangam + structural), harness fixtures.

**Merge order:** A-γ → A-α → A-β (A-β's verdict work reads A-α's valence output shape). A-0 merges
any time. Rebuild required after merge (A-α/A-γ change writers).

## FROZEN §F2 — must_not_touch (all lanes)
- FROZEN orchestrator contract (CLAUDE.md §N.2) — PARK class.
- Anything in D-1.5b/D-2/D-3/D-4 scope (chalit, vidhi, CGM/mechanism, ka_* convergence internals
  beyond A5's tests, calibration).
- CR-23 NBRY doctrine (grounds-only stands).
- `dosha_label` computation semantics (D-1.5b B9 + D-2) — only the A-β presentation guard.

## §B — BIND-AT-OPEN slots (re-verify, 10 min)
- B-1: confirm the file:line anchors above still match `main` HEAD (D-1.5 rework may have partially
  started elsewhere; if `compute_valence` already honors precedence, A1 collapses to verification).
- B-2: probe `judgment_query(wealth)` + `bodha_signals_get(wealth)` + both yoga faces on 482012f1 —
  confirm the Lane A-0 canonical baseline (reds #1–#5, #7–#9, #11; greens #10, #12; #6 split) still
  reproduces; any already-green assertion moves that item to verification-only.
- B-3: record rollback pin (deployed image SHA + build_ids both charts).

## §G — Gate (runs per CONDUCTOR_PROTOCOL §2 step 7)
Register §K.2 assertions 1–12 + A5's two-chart divergence + A7's aspect spot-check, all green on
the deployed connector after rebuild of both charts. **Final proof:** 482012f1
`judgment_query(wealth)` verdict ≠ `convergent_moderate`/composite ≠ 1.15, `bearing_yogas` contains
Dhana Yoga naming Venus (2L) + Jupiter (9L). If the number does not move, the wave did not happen.
