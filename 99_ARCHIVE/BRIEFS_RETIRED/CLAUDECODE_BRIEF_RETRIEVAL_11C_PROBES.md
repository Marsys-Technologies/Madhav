---
brief_id: RETRIEVAL_11C_PROBES
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-29
authored_for: Claude Code execution
session_type: diagnostic-only — NO code changes, NO deploys, NO tests
related_plan: 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md
parallel_stream_note: |
  A separate UI/UX modernization stream is actively running via the default
  CLAUDECODE_BRIEF.md at the project root. That brief and its scope are OFF
  LIMITS for this session. This brief governs ONE session only and produces
  ONE artifact: a diagnostic output file. It must not touch any source code.
estimated_time: 10–15 minutes

may_touch:
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_PROBES.md   # status update only, end of session
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_<DATE>.txt          # CREATE (output capture)
  # Read-only references:
  - platform/scripts/retrieval_diagnostic_probes.sql                   # READ ONLY — run via psql
  - platform/scripts/start_db_proxy.sh                                 # READ + EXECUTE only (background)

must_not_touch:
  - CLAUDECODE_BRIEF.md                                                # ROOT-LEVEL — belongs to UI/UX stream
  - 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md          # reference only; no edits
  - platform/src/**                                                    # ALL source code off-limits
  - platform/src/components/**                                         # UI/UX scope
  - platform/src/app/**                                                # UI/UX scope
  - platform/src/hooks/**                                              # UI/UX scope
  - platform/src/lib/**                                                # backend; out of scope this session
  - platform/scripts/retrieval_diagnostic_probes.sql                   # do not edit; only run
  - Any migration file under platform/migrations/**                    # no schema changes
  - Any Cloud Run service                                              # no redeploy
  - Any Cloud Build trigger                                            # no rebuild
  - Any test runner (npm test, vitest, jest)                           # do not run

acceptance_criteria:
  AC.1: Cloud SQL Auth Proxy reachable on 127.0.0.1:5433 (existing proxy reused if up; otherwise started fresh).
  AC.2: psql executes platform/scripts/retrieval_diagnostic_probes.sql to completion.
  AC.3: Full psql stdout+stderr captured to 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_<YYYY-MM-DD>.txt.
  AC.4: Output file contains the SUMMARY TABLE block at the end (probes ran end-to-end; or the file documents which probe errored and why).
  AC.5: A short structured summary is printed in the session output containing per-probe headline numbers (or per-probe error reason).
  AC.6: This brief's frontmatter status is updated to COMPLETE.
  AC.7: No source files modified. No deploys. No tests run.
---

# CLAUDECODE_BRIEF — RETRIEVAL_11C_PROBES

## §1 — Purpose

The native is running a parallel UI/UX modernization stream. The retrieval-pipeline analysis stream needs ground-truth data on Cloud SQL ingest state before its first implementation brief can be scoped. This session runs a pre-existing read-only SQL probe file and captures the output. **Nothing else.**

## §2 — Background (read this; do not act on it)

The companion plan document `00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md` enumerates 30+ candidate fixes across the 10 retrieval tools. The optimal first implementation brief depends on which probes confirm or refute the static-analysis hypotheses. You are not implementing any fix this session — you are gathering the input that determines which fix to implement next.

The probe file is at `platform/scripts/retrieval_diagnostic_probes.sql`. It contains 10 probes (PROBE 1–10) plus a SUMMARY TABLE. It is strictly read-only SQL (SELECT only). It does not modify any data.

## §3 — Execution steps

### §3.1 — Pre-flight

1. Confirm `gcloud auth` is active and project is `madhav-astrology`:
   ```
   gcloud config list account --format="value(core.account)"
   gcloud config list project --format="value(core.project)"
   ```
   Both must return non-empty values. If either is empty, halt and report — the native must authenticate.

2. Confirm Application Default Credentials are set (the Auth Proxy needs them):
   ```
   gcloud auth application-default print-access-token > /dev/null && echo "ADC OK" || echo "ADC MISSING"
   ```
   If `ADC MISSING`, halt and report; the user needs to run `gcloud auth application-default login`.

### §3.2 — Auth Proxy

1. Probe whether an Auth Proxy is already running on 127.0.0.1:5433:
   ```
   nc -z 127.0.0.1 5433 && echo "PROXY UP" || echo "PROXY DOWN"
   ```
2. If `PROXY UP`, reuse it. Skip to §3.3.
3. If `PROXY DOWN`, start it via the existing script and wait for readiness:
   ```
   bash platform/scripts/start_db_proxy.sh &
   PROXY_PID=$!
   # Poll readiness for up to 20 seconds
   for i in $(seq 1 20); do
     nc -z 127.0.0.1 5433 && break
     sleep 1
   done
   nc -z 127.0.0.1 5433 || (echo "PROXY FAILED TO START"; kill $PROXY_PID 2>/dev/null; exit 1)
   ```
4. Note the proxy PID so it can be cleaned up at end-of-session if it was started by this session.

### §3.3 — Run probes

1. Compute the output filename:
   ```
   DATE=$(date +%Y-%m-%d)
   OUT="00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_${DATE}.txt"
   ```
2. Run the probes file via psql, capturing both stdout and stderr to the output file. Use `ON_ERROR_STOP=off` so a missing column or table on one probe does not abort the rest:
   ```
   PGPASSWORD="" psql \
     -h 127.0.0.1 -p 5433 \
     -U amjis_app -d amjis \
     -v ON_ERROR_STOP=off \
     -f platform/scripts/retrieval_diagnostic_probes.sql \
     > "$OUT" 2>&1
   echo "Exit code: $?" >> "$OUT"
   ```
   - The connection user is `amjis_app`; the database is `amjis`. These match the `start_db_proxy.sh` script's connection string.
   - If `amjis_app` requires a password and `PGPASSWORD` is not set, the connection fails. In that case, retrieve the password via:
     ```
     gcloud secrets versions access latest --secret="amjis-app-db-password" --project=madhav-astrology 2>/dev/null
     ```
     and prepend it as `PGPASSWORD=<secret>` to the psql command. If no such secret exists, halt and report — the native will provide credentials.
3. Confirm the output file is non-empty and contains the SUMMARY TABLE marker:
   ```
   test -s "$OUT" && grep -q "SUMMARY TABLE" "$OUT" && echo "OUT OK" || echo "OUT INCOMPLETE"
   ```

### §3.4 — Summary

Read `$OUT` end-to-end. Produce a structured summary in the session output containing exactly these sections, one paragraph each:

- **PROBE 1** — top 3 starved (domain, planet, forward_looking) cells; total starved-cell count.
- **PROBE 2** — whether `signal_type` and `temporal_activation` columns are populated; if not, which probe lines errored.
- **PROBE 3** — valid edge_type breakdown (counts per type) and top 3 source nodes by out_degree.
- **PROBE 4** — orphan_reason breakdown and target-namespace breakdown (especially: how many orphans target `UCN.*`).
- **PROBE 5** — full layer × doc_type × chunks table.
- **PROBE 6** — per-tool zero_result_runs count over the last 20 audit_events.
- **PROBE 7** — whether `query_plans` table exists, and (if it does) which fields the classifier is consistently leaving NULL/empty.
- **PROBE 8** — count of trace steps in last 24h; any step with `status='done' AND item_count=0` is a silent zero-result tool — list them.
- **PROBE 9** — chart_facts category breakdown.
- **PROBE 10** — life_events category breakdown + sade_sati_phases coverage.
- **SUMMARY TABLE** — verbatim copy of the SUMMARY TABLE block.

Do **not** offer fixes or recommendations in the session output. The plan document already enumerates fixes; the native will pick the next brief based on the data.

### §3.5 — Close

1. If this session started the proxy (§3.2 step 3), terminate it:
   ```
   kill $PROXY_PID 2>/dev/null
   ```
   If the proxy was already running at session start (§3.2 step 2), leave it alone.
2. Set this brief's frontmatter `status: COMPLETE`.
3. Print the absolute path of the output file in the closing message:
   ```
   /Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_<DATE>.txt
   ```

## §4 — Hard constraints

- **Read-only on source.** No file under `platform/src/**` may be edited, period. If you find yourself reaching for an Edit tool against `platform/src/**`, stop and re-read this brief.
- **Probe file is canonical.** Do not edit `platform/scripts/retrieval_diagnostic_probes.sql`. If a probe errors, capture the error and continue; do not rewrite the SQL.
- **No deploys, no tests.** Do not run `npm test`, do not run `gcloud run deploy`, do not run Cloud Build. This session produces one .txt file and updates this brief's frontmatter status.
- **UI/UX scope is invisible to this session.** Do not open files under `platform/src/components/**`, `platform/src/app/**`, or `platform/src/hooks/**`. Do not touch `CLAUDECODE_BRIEF.md` at the project root.
- **One artifact created.** The only new file you create this session is `00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_<DATE>.txt`. No other writes.
- **If anything halts you** (gcloud not authenticated, proxy can't start, db connection refused, secret not retrievable), do not improvise. Print the exact error, leave the system unchanged, and stop. The native will resolve the blocker and re-run.

## §5 — Closing checklist

Verify before claiming COMPLETE:

- [ ] `RETRIEVAL_PROBE_RESULTS_<DATE>.txt` exists in `00_ARCHITECTURE/BRIEFS/` and contains the SUMMARY TABLE marker.
- [ ] Structured summary printed to session output (10 probe sections + SUMMARY TABLE verbatim).
- [ ] No file under `platform/src/**` modified (verify with `git status` — only the new .txt and this brief should appear).
- [ ] No tests, no deploys, no migrations run.
- [ ] If proxy was started by this session, it is terminated.
- [ ] This brief's `status:` is updated to `COMPLETE`.

---

*End of CLAUDECODE_BRIEF_RETRIEVAL_11C_PROBES. Status: PENDING. After execution: status: COMPLETE.*
