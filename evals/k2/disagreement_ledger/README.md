# evals/k2/disagreement_ledger

Runtime output directory for `evals/k2/auditor.ts` (LAW per `TWO_PASS_GRADING_LAW_v1_0.md`).
Each two-pass run writes one `<domain>_<chart8>_<timestamp>.json` ledger here — the audit trail
of grader/auditor disagreements, always logged and never silently resolved in the grader's
favor. Generated files are gitignored; this README + `.gitkeep` keep the directory itself
tracked so a fresh checkout has somewhere to write to.
