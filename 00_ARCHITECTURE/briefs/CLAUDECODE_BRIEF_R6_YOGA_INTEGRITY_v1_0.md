---
canonical_id: CLAUDECODE_BRIEF_R6_YOGA_INTEGRITY
version: 1.0
status: READY-FOR-KICKOFF — Wave A (build-side yoga & cancellation) gates the native rebuild
created: 2026-07-11
author: Cowork (Opus) — the yoga-integrity campaign, native-directed after the Fable-5 audit + native
  hand-analysis of chart 482012f1 (2026-07-09/10)
program: fixes the crisis in MARSYS_DEFECT_GAP_REGISTER_v2_0.md Section 1 (Y-1…Y-6). The layer users
  touch first is the weakest; this is the highest-priority block before the native chart is rebuilt.
governing_register: MARSYS_DEFECT_GAP_REGISTER_v2_0.md (LIVING) — scope drawn from it; statuses updated back to it.
scope_ruling (native): two charts (482012f1 Abhisek · 1c826d5a Abhinandan). Wave A = BUILD-SIDE fixes
  (writers → require a rebuild to correct the DATA). Serving-side items (Y-2 wire ga_yoga_firings, S-1
  special-states join, and the rest of Sections 2/4) are Wave B — no rebuild needed — and are OUT of
  Wave A scope. The native chart is rebuilt ONCE, after Wave A + Abhinandan re-zero.
lead_intelligence: FABLE 5 authors the detection/cancellation logic (it ran the coverage audit and
  proved the right mind for it). Pratinidhi-R (dossier-grounded) rules every classical choice —
  which rules, which aliases, which citations — canonical-or-citation, never a guess.
execution_mode: conductor + isolated-worktree lanes + verifier ring (≠ implementer) + Fable-5 detection
  author + Pratinidhi-R astrological authority. Deterministic-first: the writers are PYTHON, no
  generative LLM in the build path (Fable-5 designs the logic; the code that runs is deterministic).
  Per-phase prod deploys, prod-verified. Terminal cleanup = exit gate.
halt_conditions: any writer completing with 0 rows · any fabricated/vacuous fire reintroduced ·
  a bhanga/yoga rule shipped WITHOUT a classical citation or an explicit floor · chart-data write to
  482012f1 before the native-rebuild phase · canary regression with failed rollback.
may_touch: ["ga_yoga_writer.py + ga_structural_writer.py (yoga + cancellation evaluators)", "bo_laksana.py (D9 cross-check)", "bodha_writers/formulas.py (bhanga boost feed)", "l0_yogas.py catalog seed (rule/citation corrections only, versioned)", "surgical migrations (full-path cited)", "tests", "00_ARCHITECTURE run/ledger docs + register status updates"]
must_not_touch: ["orchestrator/planner core (FROZEN)", "retrieval/serving surfaces (that is Wave B)", "chart data 482012f1 before the native-rebuild phase", "LEL rows", "salience/priors CONSTANTS (the bhanga BOOST value is a registry/formula constant — feed it, don't re-pick it)", "battery/grading criteria"]
---

# BRIEF R6 WAVE A — YOGA & CANCELLATION INTEGRITY (build-side; gates the native rebuild)

**The crisis, in one line:** the layer users touch first serves fabricated yogas and cannot see
cancellations — so a chart's most common question ("do I have a raja yoga / is this affliction
cancelled?") runs on absent or wrong data. The native caught it on his own chart (Saturn mis-read as
"broken_promise" when it is neecha-bhanga-redeemed; NBRY invisible). Wave A makes yoga detection and
cancellation REAL in the build, so the corrected data can land in the rebuild.

## PHASE R6A.0 — PREFLIGHT + AUTHORITY SETUP
- Confirm register v2.0 status: Y-1/Y-7/Y-9 already FIXED (verify Y-1 fabrication-kill is live and did
  NOT regress in the Abhinandan clean-baseline build). Y-2…Y-6 OPEN — Y-3/Y-4/Y-5/Y-6 are Wave A;
  Y-2 is Wave B (serving).
- Spawn Fable-5 as detection-logic author + Pratinidhi-R on the R5_AUTHORITY_DOSSIER (extend its shastra
  map with the yoga/bhanga rule set). Open R6A_RUN_LEDGER.
- **Governing discipline for every rule below: canonical-or-citation.** Each yoga relation and each
  bhanga rule ships with its classical source (BPHS / Phaladeepika / Saravali / Jaimini Sutras, chapter+
  verse or catalog chunk_id) OR is floored NULL-with-reason. No uncited rule fires. Pratinidhi-R rules
  aliases + false-positive tolerance per rule; logged.

## PHASE R6A.1 — THE CANCELLATION ENGINE (Y-5 generic + Y-3 NBRY) — the core
- **Generic cancellation evaluator** consuming the catalog's existing dead columns
  (`cancellation_conditions`/`weakened_if`/`bhanga`/`excluded`, l0_yogas.py) for EVERY yoga — not just
  Kemadruma. Output per yoga: `bhanga_active` (bool) + which rule fired + citation + constituent fact_ids.
- **Neecha Bhanga (Y-3), all 5 classical rules, PER-VARGA (D1 AND D9+):** (1) dispositor of the
  debilitation sign in a kendra from lagna OR Moon; (2) the graha that exalts in the debilitation sign in
  a kendra from lagna OR Moon **[the native's Sun-in-D9-kendra case — this rule MUST fire on 482012f1]**;
  (3) debilitated graha aspected by its debilitation-lord or exaltation-lord; (4) conjunction with the
  exalted-therein graha; (5) mutual kendra of debilitation-lord and exaltation-graha. Each rule per varga,
  each cited. Where a bhanga forms, emit a `neecha_bhanga_raja_yoga` firing with grade.
- **GOLDEN GATE (the native's catch is the test):** on 482012f1, rule (2) fires for Saturn in D9 (Sun in
  Cancer = D9 lagna kendra) → a neecha_bhanga firing exists. On a control chart with no bhanga, none fires.
  Deterministic, in the test suite, blocking.

## PHASE R6A.2 — HOUSE-LORD YOGA FAMILY (Y-4)
- Real relation-evaluator for the ~30 house-lord relations currently `relation_unimplemented` /
  skip-listed: Viparita (Harsha/Sarala/Vimala), Dhana (2/5/9/11 combinations), Kendra-Trikona Raja,
  Dharma-Karmadhipati, Daridra, Kala-Sarpa (relation form), Shakata. Revive+correct the legacy
  `YOGA_LIBRARY` logic OR write fresh — Fable-5's call, Pratinidhi-R cites each. Remove the false
  skip-list comment ("ga_structural handles these" — it does not).
- Each firing carries constituent fact_ids + citation + (where applicable) its bhanga from R6A.1.

## PHASE R6A.3 — D9 CROSS-CHECK CONSULTS CANCELLATION (Y-6)
- `bo_laksana.py` D9 cross-check: BEFORE emitting `broken_promise`, consult the R6A.1 bhanga result for
  that graha/varga. If cancelled → emit `redeemed`/`neecha_bhanga` classification, NOT `broken_promise`.
- Feed the real `neechabhanga_modifier` / `cancellation_modifier` (kill the hardcoded 1.0) and let the
  existing 1.3 salience bhanga boost (formulas.py) finally receive a non-1.0 input.
- **GOLDEN GATE:** on 482012f1, Saturn's D9 cross-check emits redeemed/neecha_bhanga — NOT
  broken_promise. (This is the exact inversion the native caught; it is the acceptance proof.)

## PHASE R6A.4 — VERIFY Y-1 HOLDS + HONESTY
- Confirm the vacuous-pass fabrication kill (Y-1) is live: no `requires_pass` blanket fire, no garbage
  OCR names, no contradictory pairs. `ga_yoga_firings` is the honest source of truth (its wiring to
  serving is Wave B; here we only ensure the BUILD writes it correctly).
- Anti-fabrication test: a deliberately-unevaluable catalog row does NOT fire (floors explicit).

## PHASE R6A.5 — RE-ZERO ON ABHINANDAN (guarded rebuild, the proving ground)
Deploy Wave A to the build-job image (verify image SHA == merge SHA — deploy-truth). Then, via the
Nirmāṇa build tracker + Chrome MCP, guarded global Rebuild of Abhinandan `1c826d5a` (the flow proven in
the last session: Guardian watches SSE + Cloud Run logs, no completed-with-0, fix-and-redeploy on
failure). Gates: all assets `lit` 0-error; **yoga surface REAL** (no fabricated names, no contradictory
pairs, `ga_yoga_firings` populated with citations); house-lord yogas detected where present; cancellation
evaluator ran. Report before touching the native.

## PHASE R6A.6 — THE NATIVE REBUILD (the one shot, on corrected architecture)
Only after R6A.5 passes. Fresh snapshot of 482012f1 (exact-count-verified, per the truncation lesson) →
guarded global Rebuild via Nirmāṇa. Post-rebuild gates: FORENSIC 7/7 ×5 · 57 LEL rows intact +
calibration_state='calibrated' + 10:43 held · **THE NATIVE'S GOLDEN CATCHES: (a) NBRY fires for Saturn
(D9 rule-2); (b) Saturn's D9 cross-check reads redeemed/neecha_bhanga, NOT broken_promise; (c) yoga
surface real, no fabrication** · degeneracy sweep · retrievability spot-probes. If any golden catch
fails → HALT, restore from snapshot, report (the fix didn't land). No iteration on the native chart.

## PHASE R6A.7 — CLOSE
Register v2.0: Y-3/Y-4/Y-5/Y-6 → FIXED with evidence; Y-1 re-confirmed. Ledger + CURRENT_STATE +
SESSION_LOG close. Worktree/branch cleanup (exit gate). Report to native, leading with the three golden
catches. Wave B (serving-side: Y-2 wire ga_yoga_firings, S-1 special-states join, per-varga surfacing)
is the next brief — no rebuild, so it follows freely.

## ANTI-GOALS
NO uncited yoga/bhanga rule (canonical-or-citation, always). NO generative LLM in the writer (Fable-5
designs; deterministic Python runs). NO serving-side work (Wave B). NO native rebuild before the
Abhinandan re-zero passes. NO re-picking the bhanga boost constant (feed the existing one). NO
fabrication reintroduced. The native's own two catches are the acceptance test — if Saturn still reads
"broken_promise" after R6A.6, Wave A has NOT succeeded, regardless of what else is green.
