---
artifact: ANSWER_EVAL_BASELINE_KICKOFF_v1_0.md
brief_id: ANSWER_EVAL_BASELINE
version: 1.0
status: READY
authored_at: 2026-06-01
authored_by: cowork-planner
surface: operator/executor runs against production. Read-only eval (no writes).
why: >
  Post PyJHora-arc + forensic-render delivery, the corpus is finally whole. Run the
  consolidated answer:eval to get a fresh baseline (pass rate, B.11 coverage, citation rate,
  calibration). v5.68 next-objective item.
sequencing_note: >
  Forensic content is NOT RAG-retrievable until RAG_CHUNKS_CHART_ID_KEYING lands (forensic
  chunks never reached rag_chunks — schema drift). For a forensic-INCLUSIVE baseline, run this
  AFTER that fix. For a pre-fix baseline (to measure the lift the fix gives), run it now and
  again after. Either is fine — just label which.
prior_baseline: "2026-05-04 — pass 8%, B.11 94%, citations 14%, calibration 39% (project_ganga_baseline)"
---

# answer:eval baseline — kickoff

Consolidated run only (per `[[retrieval-tools-consolidated-eval]]` — not per-PR). Needs a
valid `__session` cookie; the harness 401s without it (that was the v5.68 step-7 "0/15").

## Run it

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# 1. Mint a __session cookie for an authorised user
COOKIE=$(npx tsx platform/scripts/dev/mint_session_cookie.ts)   # emits __session=...

# 2. Run the 15 golden queries against production
BASE_URL=https://amjis-web-938361928218.asia-south1.run.app \
AUTH_TOKEN="$COOKIE" \
npx tsx scripts/answer_eval.ts | tee 00_ARCHITECTURE/eval_runs/answer_eval_$(date +%Y%m%d).log
```

## Record

Append to `project_ganga_baseline` tracking (and CURRENT_STATE next-close): date, pass rate,
B.11 coverage, citation rate, calibration — and whether forensic-inclusive (post RAG-KEY) or
pre-fix. Compare against the 2026-05-04 prior baseline; call out any regression or lift.

## Watch for

- 401 → cookie missing/expired; re-mint.
- Low citation rate on forensic queries pre-RAG-KEY is EXPECTED (forensic not yet in
  rag_chunks) — not a corpus-quality signal; re-measure post-fix.

---

*End of ANSWER_EVAL_BASELINE_KICKOFF_v1_0.md*
