---
artifact: L4_PHALA_AUDIT_v1_0.md
canonical_id: L4_PHALA_AUDIT
version: 1.0
status: CURRENT — code-verified reality check that opens the L4 Phala campaign
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The audit-first deliverable for L4 Phala. Verifies the 5 registered ph_* placeholders,
  the pre-existing legacy phala code, the migration-numbering reality, and the DAG against
  the LIVE repo — NOT the handoff's claims. Mirrors the L3 method (don't trust the seed or
  the handoff; code-verify). Three handoff corrections are recorded here with evidence.
supersedes: none
inputs_verified_against:
  - platform/scripts/seed/asset_registry_seed.ts (ph_* block, lines ~1437-1522)
  - platform/scripts/migrate.ts (two-directory merge logic)
  - platform/supabase/migrations/ + platform/migrations/ (the two interleaved series)
  - platform/python-sidecar/brahmagyan/phala/l4_*.py (legacy WS-2 build)
  - platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py (frozen-contract house-style)
  - 00_ARCHITECTURE/CONDUCTOR/ws2/smriti/l4-phala-pass.md (legacy seal record)
  - 00_ARCHITECTURE/L3_KALA_CLOSE_v1_0.md §11 (L4 onboarding contract)
---

# L4 Phala — Audit / Reality Check v1.0

> **Method note.** L3 taught that the handoff's "engines exist, just wire" was FALSE — the
> heart was unbuilt. So every claim in `L4_PHALA_CONVERSATION_HANDOFF_v1_0.md` was re-verified
> against the live tree on branch `fix/l3-cockpit-ui-service-pill-and-floor`. The handoff is
> accurate on the big picture and on the placeholder registration, but carries **three material
> errors** (§3). This doc is the corrected ground truth the campaign plan builds on.

---

## §1 — What is genuinely TRUE in the handoff (verified)

| Claim | Verdict | Evidence |
|---|---|---|
| L0→L3 all SEALED; L4 Phala is next | ✓ TRUE | `CURRENT_STATE_v1_0.md` v5.89; `L3_KALA_CLOSE_v1_0.md` v1.1 (prod-built, cockpit-verified rev `amjis-web-00664-xc6` + localhost:3002) |
| 5 `ph_*` placeholders registered, `is_active:true` | ✓ TRUE | `asset_registry_seed.ts` lines ~1437-1522 — all 5 present |
| `count_sql` uses `$1` binding (not the `$$CHART_ID$$` L3 bug) | ✓ TRUE | each ph_* row: `SELECT count(*) FROM phala_* WHERE chart_id = $1` |
| DAG wired in the seed | ✓ TRUE | ph_nimitta←ka_sangam; ph_muhurta←ka_kalasutra+ga_panchanga; ph_sodhana←bo_laksana; ph_pratikara←bo_upaya+ka_vighnakara; ph_suddha_sodhana←ph_sodhana |
| Tables + writers do NOT yet exist | ✓ TRUE | no `phala_*` table migration in `supabase/migrations/`; no `ph_*` writer under `pipeline/orchestrator/writers/` |
| L4 reads kala_*/bodha_*/chart_facts read-only, writes only phala_* | ✓ TRUE (contract) | `L3_KALA_CLOSE §11`; enforced by anti-drift grep gate |
| Ratified I-7/I-8/I-16/I-17 inherited unchanged | ✓ TRUE | `L3_KALA_CLOSE §9`; `L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md` |
| First L4 migration should drop deprecated `kala_timeline` (CF.L3.2) | ✓ TRUE | mig 246 COMMENT marks it DEPRECATED |

The registered `ph_*` block (verbatim intent):

| asset_id | sanskrit | english | target_table | depends_on |
|---|---|---|---|---|
| `ph_nimitta` | Nimitta | Predictive anchors | `phala_anchors` | `ka_sangam` |
| `ph_muhurta` | Muhūrta | Auspicious windows | `phala_muhurta` | `ka_kalasutra`, `ga_panchanga` |
| `ph_sodhana` | Śodhana | Rectification | `phala_rectification` | `bo_laksana` |
| `ph_pratikara` | Pratīkāra | Mitigation | `phala_mitigation` | `bo_upaya`, `ka_vighnakara` |
| `ph_suddha_sodhana` | Śuddha-śodhana | Best rectification | `phala_rectification_best` | `ph_sodhana` |

---

## §2 — The frozen-contract house-style (verified from a sealed L3 writer)

`ph_*` writers MUST replicate `pipeline/orchestrator/writers/ka_sangam.py` exactly:

- `@register('<asset_id>')` decorator; subclass `WriterBase`; class attr `asset_id`.
- `run(self, ctx) -> WriterResult` (light) OR `plan_substeps`/`run_substep` (heavy).
- `conn = ctx.db_conn` — **orchestrator owns the transaction; writer NEVER `.commit()`/`.rollback()`/`.close()`**.
- `chart_id = ctx.config['chart_id']`.
- **Idempotency:** `DELETE FROM phala_* WHERE chart_id = %s` then insert (delete-then-insert, §N.3).
- Return `WriterResult(asset_id='<id>', rows_inserted=N)` — note the kwarg is **`rows_inserted`**, NOT `rows_written` (that exact mismatch was L3 BUG-3 across 5 writers).
- Pure computation lives in a separate `services/<asset>/engine.py`; the writer only orchestrates I/O.
- A standalone `run_<asset>_prod.py` exists for operator prod runs (bypasses orchestrator build-state — see CF.L3.8: future rebuilds MUST use the orchestrator click-Build path).

---

## §3 — The THREE handoff corrections (code-verified, with evidence)

### CORRECTION 1 — Migration numbering: the handoff's "251+" is UNSAFE; use **330+**

The handoff (§5.5) and `L3_KALA_CLOSE §11.5/.10` say "L4 starts at migration 251+." This is **wrong and collision-prone**. Evidence:

- `migrate.ts` (lines 1-12, `collectMigrationFiles`) reads **BOTH** `platform/migrations/*.sql` **AND** `platform/supabase/migrations/*.sql`, merges them, and applies in **lexical filename order**. Tracking is by full `filename` in `_migrations_applied`.
- L3 lives in `supabase/migrations/`, which ends at **250** (`250_l3_count_sql_param_fix.sql`). True — but that is only one of the two series.
- `platform/migrations/` is a **separate, active series** that reaches **329** (`329_ka_transit_almanac_hard_remove.sql`).
- Cross-directory number collisions ALREADY exist at **174, 223, 239, 240, 250** — i.e. two files share a number across the two dirs and coexist only because tracking is by full filename.
- A new L4 file named `251_*.sql` in `supabase/migrations/` would be globally ambiguous: `platform/migrations/251..329` already occupy that range, and lexical interleaving of the two dirs makes "what runs before what" fragile.

**Resolution (collision-safe):** L4 pre-allocates migration numbers **starting at 330**, placed in `platform/supabase/migrations/` (the orchestrator-native path L3 used). This clears the global max across both interleaved series. This is exactly the documented **"two-174 trap"** the L3 session-queue PRE-2 step warns about — L4 must run the same pre-allocation step.

> **Action for the campaign:** the Conductor pre-fan-out step PRE-2 confirms the global max across BOTH dirs and pre-allocates the L4 numbers (≥330) in DAG order before any agent spawns.

### CORRECTION 2 — A substantial LEGACY L4 phala build EXISTS (handoff is silent)

The handoff describes L4 as "5 registered placeholders, all UNBUILT, empty tables." That is true for the **orchestrator-native** L4. But a complete **pre-rebuild** L4 build exists from **2026-06-05** (WS-2 era) that the handoff never mentions:

- Writers: `platform/python-sidecar/brahmagyan/phala/l4_anchors.py`, `l4_mitigation.py`, `l4_muhurta.py`, `l4_rectification.py`, `l4_outlook.py` (+ Phase-4C-era `anchors.py`/`mitigation.py`/etc.).
- Migrations: `platform/migrations/brahma_phala_anchors.sql`, `brahma_phala_mitigation.sql`, `brahma_phala_muhurta.sql`, `brahma_phala_rectification.sql`.
- MCP tools: `platform-mcp/src/tools/phala_event_anchors.ts`, `phala_mitigation_map.ts`, `phala_muhurta_finder.ts`, `phala_outlook.ts`, `phala_rectification.ts`.
- Seal record: `00_ARCHITECTURE/CONDUCTOR/ws2/smriti/l4-phala-pass.md` (5 assets, dot-notation `phala.*`).

**Why it is NOT the target L4:** it predates the frozen orchestrator, predates the underscore-prefix convention (`phala.anchors`, not `ph_nimitta`), is built as FastAPI routers + static embedded catalogs (not `WriterBase`/`phala_*` tables), and is grounded in the **retired** FORENSIC-v8.0-via-`forensic_render` source (deleted PR #187; live source is now `chart_facts`).

**Disposition (native decision 2026-06-21):** **audit-then-mostly-rebuild.** The *logic* is high quality and should be harvested; the *architecture* is wrong and must be rebuilt against the frozen contract. See §4 for the harvest manifest.

### CORRECTION 3 — Anchors/markers must be DERIVED, not hand-written

The legacy `l4_anchors.py` hand-wrote a 24-entry `ANCHOR_CATALOG` with hand-assigned `confidence` floats and hand-typed `SIG.MSR.018`-style signal IDs as embedded Python constants. That violates the **anti-drift / L3-is-authority** discipline (B.1 / §N.5): an L4 row must **reference** a real `ka_sangam` convergence window + its resolving L2 `signal_id` / L1 `fact_id` and inherit those values, never restate hand-authored constants.

**Resolution:** the rebuilt `ph_nimitta` **derives** anchors from `ka_sangam`'s 660 real convergence windows (`kala_convergence` rows, which already carry `signal_id`, `convergence_score`, `confidence_label`, `peak_date`), applies the harvested calibration ladder as a **deterministic transform over the real I-16 score**, and cites the real `convergence_id`/`signal_id` in its derivation ledger. Same principle for `ph_sodhana` markers (derive from `bo_laksana` + LEL, cite `signal_id`).

---

## §4 — Legacy harvest manifest (what to take, what to discard)

| Legacy asset | HARVEST (the logic) | DISCARD (the architecture) | Lands in |
|---|---|---|---|
| `l4_anchors.py` | The **calibration ladder** (single≤0.55, 2≤0.65, 3≤0.72, 3+kala≤0.78, ≥4+kala≤0.80, hard ceiling 0.80); the 6-domain taxonomy (career/relationship/financial/spiritual/health/transition); explicit-falsifier-per-anchor discipline | Hand-written catalog; hand-assigned confidences; embedded `SIG.MSR.*` constants; FastAPI router; FORENSIC-via-forensic_render source | `ph_nimitta` (ladder → deterministic transform over `ka_sangam` I-16 score) |
| `l4_rectification.py` | The **train/test leakage discipline** (pre-2020 train / post-2020 + late-disclosed-as-holdout sacrosanct, per Learning-Layer rule #4); the candidate-time grid (10:13–11:13 IST, 5-min steps); the qualitative Aries/Taurus marker analysis | The `[EXTERNAL_COMPUTATION_REQUIRED]` stub for ascendant degree (now computable — see §5); embedded TRAINING/HOLDOUT event lists (derive from LEL + `bo_laksana`); FastAPI router | `ph_sodhana` / `ph_suddha_sodhana` |
| `l4_mitigation.py` | BPHS chapter/verse citation discipline; remediation-per-obstruction structure | Static embedded catalog | `ph_pratikara` (derive from `bo_upaya` + `ka_vighnakara`) |
| `l4_muhurta.py` | The action-type × window-quality scoring shape; 6 action classes | Approximate panchanga arithmetic (use `ga_panchanga` + `ka_muhurta_seva` real values) | `ph_muhurta` |
| `l4_outlook.py` | The **composite whole-chart-read (B.11) integration** pattern — composes all L4 sub-assets into one horizon-scoped dossier | Python-import composition; static readiness score | `ph_phaladesa` (NEW composite — see campaign plan) |

---

## §5 — Rectification compute: NO LONGER external (decisive finding)

The legacy rectification stopped at a framework + a preliminary "Aries 0.72" verdict, marking the exact ascendant-degree computation `[EXTERNAL_COMPUTATION_REQUIRED]`. **That is now obsolete.** Verified:

- `platform/python-sidecar/pyjhora_adapter/houses.py::compute_ascendant(jd_ut, ayanamsha, lat, lon, tz)` returns the ascendant longitude to fractional degree at **any** Julian Day.
- `pyjhora_adapter/compute.py::compute_chart(datetime_iso, lat, lon, tz, …)` is a clean entry point taking an arbitrary wall-clock time → full ascendant.
- PyJHora is the sealed project engine (replaced `natal_engine/`; no JH-parity gate; trust by internal consistency).

**Therefore `ph_sodhana` CAN deterministically compute** the ascendant at each candidate birth time, find the real Aries→Taurus cusp crossing for 1984-02-05 Bhubaneswar, and score the train-set events against each candidate — turning the legacy framework into a **real, in-process deterministic computation** while preserving the leakage discipline. This is a `[NATIVE-RATIFY]` recommendation carried into the campaign plan (§ rectification), not a silent decision.

---

## §6 — Audit verdict

L4 Phala is genuinely **DESIGN-READY and UNBUILT** at the writer/table layer. The 5 placeholders are sound; the DAG is sound; the frozen-contract house-style is clear; the legacy code is a rich logic donor but an architectural dead-end. The campaign proceeds with: **6 assets** (5 registered + `ph_phaladesa` composite), **migrations 330+** in `supabase/migrations/`, **PyJHora-computed rectification** (native-ratify), and the **live-visual-cockpit HARD seal gate** baked in from day one (the #1 L3 lesson). Proceed to `L4_PHALA_CAMPAIGN_PLAN_v1_0.md`.

---
*End of L4_PHALA_AUDIT v1.0. Code-verified; three handoff corrections recorded with evidence.*
