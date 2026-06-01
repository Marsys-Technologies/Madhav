---
artifact: OPERATOR_LEDGER_PATCH_PYJHORA_POSTMERGE_v1_0.md
version: 1.0
status: PASTE-READY (apply at session close, per governance discipline)
authored_at: 2026-06-01
authored_by: cowork-planner
why: >
  Records the post-merge landed state of the PyJHora arc. Provided as paste-ready blocks
  rather than live edits because (a) the mounted checkout is on fix/pariksha-second-pass,
  behind origin/main v5.66, and (b) CURRENT_STATE bumps belong to a session-close
  (SESSION_CLOSE_TEMPLATE), not a side edit.
context_at_authoring:
  origin_main_current_state_version: 5.66 (PYJHORA-ENGINE-REPLACE — "branch opened for review")
  next_version: 5.67
  sidecar_revision: amjis-sidecar-00511-pz7
  web_revision: amjis-web-00494-jjd
  native_chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
  native_build_id: a494ec15
---

# Operator ledger patch — PyJHora post-merge landed state

Two paste blocks. Block A updates `OPERATOR_ACTIONS_PENDING.md`. Block B is the
`CURRENT_STATE_v1_0.md` v5.67 changelog entry to land at the next session-close.

---

## Block A — OPERATOR_ACTIONS_PENDING.md

**A.1 — Mark CRITICAL §2 (native chart build) partially done.** Under
`## CRITICAL — Multi-Ayanamsha Build`, annotate item 2:

> ### 2. Trigger native chart build — ✅ DONE 2026-06-01
> Native chart `362f9f17-95a5-490b-a5a7-027d3e0efda0` built via `marsys-build-pipeline-job`
> (build_id `a494ec15`) on the PyJHora engine (`amjis-sidecar-00511-pz7`). All 65
> `(category × ayanamsha_id)` cells non-zero in `chart_facts`. Panchanga FORENSIC
> spot-check 5/5. **NOTE:** triggered job-direct because the Cloud Tasks → `/api/build/task`
> path 401'd (see new HIGH item below). `forensic` asset is still a 0-row stub (Stream F).

**A.2 — Flip MEDIUM §"Migrations 121/122/124" from BLOCKED to READY.** Replace the
"Do NOT attempt until the Multi-Ayanamsha chart build…" line with:

> **UNBLOCKED 2026-06-01.** The native build wrote real per-`chart_id` rows to
> `chart_facts`. The `chart_id`-100%-NULL precondition is cleared. Migrations 121/122/124
> (`query_trace_steps` partitions) may now apply. Still a separate gated operator step —
> verify `chart_id` non-NULL coverage on the target tables before applying.

**A.3 — Add a new HIGH item.** After the existing HIGH section:

> ## HIGH — Build trigger path broken (Cloud Tasks → /api/build/task 401)
> The autonomous build trigger 401s in production; native build was run job-direct as a
> workaround. Fix brief:
> `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md`.
> Likely cause: `amjis-web` is private, so Cloud Run strips the OIDC `Authorization` header
> before the app's bearer parse — app should authorise on `X-CloudTasks-*` headers under
> IAM (Design A). Operator IAM/env actions listed in the brief.
>
> ### Hygiene — remove BUILD_TASK_AUTH_BYPASS from amjis-web
> The var grants nothing (code-neutralised + regression-tested) but trips a SECURITY log
> alert. Remove it:
> ```bash
> gcloud run services update amjis-web --region asia-south1 --project madhav-astrology \
>   --remove-env-vars BUILD_TASK_AUTH_BYPASS
> ```

**A.4 — Add a new HIGH item for the still-open primary target.**

> ## HIGH — Forensic render still a stub (Stream F)
> `forensic_writer.py` returns 0 rows. The PyJHora arc swapped the engine but did NOT
> deliver the forensic (A2 Pratyaksha) render — its named primary target. Scoping brief:
> `00_ARCHITECTURE/BRIEFS/STREAM_F_FORENSIC_RENDER_SCOPING_v1_0.md` (needs native decisions
> Q1/Q3 before it becomes an executor brief).

**A.5 — Add a MEDIUM item for the jh-parity residue.**

> ## MEDIUM — jh-parity residue in platform/ code paths
> PR #184 AC4/AC5 greps were scoped to python-sidecar/ only; residue remains in
> `platform/scripts/hard_gates_check.sh` (G2 gate rewards jh_oracle.json), `acc2_hard_gates.json`,
> `engine/current/route.ts` (`jh_parity_sha`), and a committed `_scratch/` file. Cleanup brief:
> `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md`.

---

## Block B — CURRENT_STATE_v1_0.md (bump version to 5.67; prepend this changelog entry)

Set frontmatter `version: 5.67`. Prepend under `changelog:` above the v5.66 entry:

```yaml
  - v5.67 (2026-06-01, PYJHORA-POSTMERGE-DEPLOY):
    **PyJHora engine LIVE in production. PR #184 (engine swap) + #186 (Dockerfile hotfix:
    libgl1-mesa-glx→libgl1 for Bookworm) merged. amjis-sidecar-00511-pz7 — clean headless
    boot (QT_QPA_PLATFORM=offscreen + lazy jhora.panchanga.drik). Native chart
    362f9f17-95a5-490b-a5a7-027d3e0efda0 built (build_id a494ec15) job-direct; all 65
    (category × ayanamsha_id) chart_facts cells non-zero; panchanga FORENSIC spot-check
    5/5. v1.3 partitions 121/122/124 UNBLOCKED (real per-chart_id rows now exist).**
    open_residuals:
      - "forensic_writer still a 0-row stub — Stream F primary target NOT delivered (STREAM_F_FORENSIC_RENDER_SCOPING_v1_0.md)"
      - "Cloud Tasks → /api/build/task 401 — build trigger path broken; bypassed job-direct (CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md)"
      - "BUILD_TASK_AUTH_BYPASS=test still set on amjis-web — remove (zero effect, trips SECURITY alert)"
      - "jh-parity residue in platform/ code paths — AC4/AC5 greps were python-sidecar-scoped (CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md)"
    files_touched: ["platform/python-sidecar/Dockerfile", "00_ARCHITECTURE/CURRENT_STATE_v1_0.md", "00_ARCHITECTURE/OPERATOR_ACTIONS_PENDING.md", "00_ARCHITECTURE/SESSION_LOG.md"]
    active_phase_plan_sub_phase: M6 INCOMING (post-merge deploy session; no macro-phase change).
    last_session_id: PYJHORA-POSTMERGE-DEPLOY. predecessor_session: PYJHORA-ENGINE-REPLACE.
    carry_forwards: ["Stream F forensic render (4 follow-on briefs authored 2026-06-01)", "build-task 401 fix", "121/122/124 partition apply (now unblocked, separate gate)"]
    next_session_objective: "Native decides Stream F Q1/Q3; execute build-task 401 fix; apply 121/122/124."
    file_updated_at: 2026-06-01. file_updated_by_session: PYJHORA-POSTMERGE-DEPLOY.
```

> **Honesty note for the close session:** the v5.66 entry says the arc "COMPLETE … panchanga
> spot-check PASS 5/5." That is true for the engine swap but the entry does not record that
> `forensic` — the brief's named primary target — is still a stub. v5.67's `open_residuals`
> corrects the ledger so "PyJHora COMPLETE" is not read as "forensic delivered."

---

*End of OPERATOR_LEDGER_PATCH_PYJHORA_POSTMERGE_v1_0.md*
