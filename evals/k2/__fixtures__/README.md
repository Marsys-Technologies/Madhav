# evals/k2/__fixtures__

Small **synthetic** transcripts used only to smoke-test the K2 grading scripts in this
directory (not real harness output — the real thing lives in `evals/omega7/harness_runs/`
on the Ω7 lane, or in future sealed-harness runs this campaign produces). Kept intentionally
tiny so `npx tsx evals/k2/run_k2_battery.ts --smoke` runs in well under a second.

- `wealth_smoke.transcript.json` — one `ganita_chart_facts_get` call whose `result_raw`
  contains a handful of real fact_ids drawn from `COMPLETENESS_ACCOUNTING_wealth_482012f1_v1_0.json`
  (so consumption_ratio scores a small nonzero hit), plus a `final_answer` string exercising
  the honesty-completeness and volunteered-findings checks.
