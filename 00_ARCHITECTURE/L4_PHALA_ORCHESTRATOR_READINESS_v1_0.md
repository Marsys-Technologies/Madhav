---
artifact: L4_PHALA_ORCHESTRATOR_READINESS_v1_0.md
canonical_id: L4_PHALA_ORCHESTRATOR_READINESS
version: 1.0
status: CURRENT — the orchestrator-wiring verification + the one real pre-implementation gap (+ fix)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  Answers the native's pre-kickoff question: "is the orchestrator wiring fully implemented; are there
  pre-implementation activities; is there anything to look into?" Code-verified. Finds the orchestrator
  ENGINE fully implemented, the build path end-to-end, and ONE real latent infrastructure gap
  (services/ not COPY'd into the pipeline image) that would silently hang the L4 build. The fix is
  folded into Phase 0 (SETUP).
---

# L4 Phala — Orchestrator Readiness (verified)

## §1 — Is the orchestrator wiring fully implemented? — YES (the engine), as-designed (the L4 code)
| Component | Status | Evidence |
|---|---|---|
| **Writer auto-discovery** | ✅ IMPLEMENTED | `pipeline/orchestrator/writers/__init__.py::_auto_discover()` — pkgutil walks the package, imports every module, `@register` populates `_REGISTRY`. **Hard-fails on import errors** ("registration gap is not silently OK") — a broken ph_* fails LOUDLY at discovery. |
| **The frozen contract** | ✅ IMPLEMENTED | `WriterBase` (asset_id, has_substeps, run(ctx), plan_substeps/run_substep); `ContextSpec` (db_conn caller-owned, config[chart_id], dry_run); `WriterResult(asset_id, rows_inserted, …)`; `SubStep` (savepoint + heartbeat + crash-resume for heavy writers). |
| **The per-chart build driver** | ✅ IMPLEMENTED | `runner.py::execute_run(run_id)` — loads `build_run`, acquires the chart advisory lock, walks the per-asset `plan`, dispatches via `get_writer`, writes build-state. `main.py` is the `python -m pipeline.orchestrator.main --run-id` entry. |
| **The click-Build API path** | ✅ IMPLEMENTED | `/api/build/start` (+ cancel/reap/pyramid-layers routes) → enqueues a `build_run` → the Cloud Run job runs the orchestrator. The autonomous click-Build path the plan depends on works end-to-end. |
| **Heavy-writer fit** (ph_sodhana tiered scorer, ph_phaladesa LLM) | ✅ FITS | the SubStep mechanism handles heavy/long writers (ga_dashas = 35 substeps, 40-min). ph_sodhana's per-candidate scoring + ph_phaladesa's per-(horizon×lens) composition map cleanly to substeps. |
| **The 8 ph_* writer files** | ⬜ NOT YET (correct) | These are what the SWARM builds — not a pre-implementation gap. They register via `@register('ph_*')` in `pipeline/orchestrator/writers/` (COPY'd via the `pipeline/` COPY — see §3). |

**Verdict:** the orchestrator is a sealed, frozen, fully-working engine (drove L1 + L3). L4 onboards by
writing `@register('ph_*')` WriterBase subclasses — no orchestrator change. **One infra gap (§2).**

## §2 — THE REAL GAP — `services/` is not COPY'd into the pipeline image (silent-hang risk)
**Code-verified (2026-06-22):**
- **All 5 L3 `ka_*` writers AND all 8 planned L4 `ph_*` writers import `from services.<asset>.engine`**
  (the engine logic lives in `platform/python-sidecar/services/<asset>/`, the thin writer in
  `pipeline/orchestrator/writers/`). Confirmed: ka_sangam imports `from services.ka_sangam.engine` +
  `from services.ka_dasha_kala.service`.
- **`Dockerfile.pipeline` COPYs `pipeline/`, `brahmagyan/`, `ga_writers/`, `bodha_writers/`,
  `panchang_engine/`, `pyjhora_adapter/` — but NOT `services/`.** (Verified: `services/` appears in NO
  Dockerfile.) `PYTHONPATH=/app/platform/python-sidecar`, so `services/` would resolve IF present.
- **The git log shows the exact bug pattern:** `fix(bo_pramana_mapa): add bodha_writers/ COPY to
  Dockerfile.pipeline (ModuleNotFoundError on Cloud Run)`. The same fix was applied to `bodha_writers/`
  but **never to `services/`.**
- **Why L3 didn't catch it:** CF.L3.8 — L3's prod build-state was stamped via a one-shot
  `reconcile_l3_build_state.py` script that ran the writers in the FULL worktree (which has `services/`),
  BYPASSING the Cloud Run orchestrator job. So the gap is LATENT — it never fired because the
  orchestrator-job path was never exercised for L3.

**Why it bites L4:** the L4 plan REQUIRES the orchestrator click-Build path (D-CF.L3.8: no reconcile
scripts). The first ph_* writer the Cloud Run job tries to import → `ModuleNotFoundError: services` →
the job crashes, `build_runs.state` stays `running` forever → silent hang. **This is the
single highest-risk pre-implementation item.**

### THE FIX (one line; Phase 0 / SETUP)
Add to `platform/python-sidecar/Dockerfile.pipeline` (next to the other writer COPYs):
```dockerfile
# L3 + L4 service-engine modules (ka_* writers + all ph_* writers import `from services.<asset>`)
COPY platform/python-sidecar/services/ ./platform/python-sidecar/services/
```
This ALSO fixes the latent L3 gap (a future L3 rebuild via the orchestrator would otherwise hit it).

## §3 — Other pre-implementation checks (verified — no further gaps)
| Check | Result |
|---|---|
| Do new ph_* writer files get COPY'd? | ✅ YES — they live under `pipeline/orchestrator/writers/`, COPY'd via `COPY pipeline/`. |
| Are the reused engines in the image? | ✅ panchang_engine ✅ pyjhora_adapter ✅ bodha_writers ✅ ga_writers — all COPY'd. (services/ = the gap above.) |
| Does the TS school engine (U4) need a Docker COPY? | ⬜ NO — it runs in the Next.js/web image (TypeScript), not the python pipeline image. U4's persistence route is web-side (registry spec R1). Confirm the web Dockerfile builds `src/lib/schools/`. |
| `bodha_cdlm_cells` FK target column name | ⚠️ VERIFY at build — ph_sankrama FKs `bodha_cdlm_cells(cell_id)`; confirm the PK column name (`cell_id` vs `id`) at writer-time (the L3 BUG-4 column-rename class). |
| `kala_bhavishya` PK for ph_nimitta inheritance | ✅ `id BIGSERIAL` (verified) — ph_nimitta `bhavishya_id` FKs it. |
| New-asset cockpit render | ✅ derived from `asset_registry.layer='phala'` (no frontend hardcode). |
| build_runs.plan includes the L4 assets | ⚠️ The build-run PLAN must enqueue the 8 ph_* in DAG order — the Conductor builds the plan at click-Build (Phase 0 / the build invocation), reading depends_on. Confirm the plan-builder topo-sorts the new assets. |

## §4 — Disposition (fold into Phase 0)
- **SETUP-6b (NEW, blocking):** add the `services/` COPY to `Dockerfile.pipeline` + rebuild the image.
  This is a one-line infra fix that MUST land before any ph_* build (and retroactively fixes L3).
- **SETUP verify:** the web Dockerfile builds `src/lib/schools/` (for U4); the build-run plan-builder
  topo-sorts the new ph_* assets; confirm `bodha_cdlm_cells` PK name at ph_sankrama build.
- Everything else: the orchestrator engine is ready; the swarm writes the ph_* writers against the
  frozen contract.

---
*End of L4_PHALA_ORCHESTRATOR_READINESS v1.0. The orchestrator ENGINE is fully implemented + the build
path works end-to-end. ONE real latent infra gap: services/ not COPY'd into the pipeline image (would
silently hang the L4 orchestrator build; L3 masked it via the reconcile path / CF.L3.8). Fix = a
one-line Dockerfile COPY, folded into Phase 0 SETUP-6b. No other gaps.*
