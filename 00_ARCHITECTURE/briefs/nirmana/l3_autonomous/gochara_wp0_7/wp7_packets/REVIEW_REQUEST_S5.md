# REVIEW REQUEST — §5 as a whole (WP9 overlays on the kernel, A-1 authorized)

**Brief:** `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` §5 (lines 133–141)
**Branch:** `l3/gochara-autonomous-wp0-7`
**Sheet items implemented:** F-11, M-8, M-4 (Kota record), WP9 steps 5.1–5.4

## What changed

- **5.1** (`a5ac0caad`): overlay stamp columns (`source_qualification`, `precision_regime`, `corpus_verifiable`) on `kala_vedha_gochara` + `kala_moorti_nirnaya` — migration **1082** (disposable-DB only); writers populate; conjuncts (a)–(j) verified on the disposable DB.
- **5.2** (`41e4843cd`): M-8 vedha exceptions in `ka_vedha_gochara` — Sun↔Saturn / Moon↔Mercury mutual exclusion (coverage record, no vedha row), vipareeta cancellation (`suppression_factor=1.0`, translator commentary), retrograde-malefic intensity qualifier; evaluation order exceptions→vipareeta; date-grain stamps preserved. 12/12 new tests.
- **5.3** (`0c876fbe4`): Vedha+Moorti on the kernel — requested-horizon coverage (F-11) via `ctx.config` horizon start/end; `gochara_kernel/overlays.py` interval-set projection (unavailable outside the searched horizon, never default 1.0; A08 one-root-once dedup; `coverage_gaps`); Moorti graded at the true kernel `sign_ingress` instant with day-grade misclassification counted; `independence_group` on all vedha rows. 14 new tests; battery 642 passed at that commit.
- **5.3 report + 5.4** (`7cca66fa2`): moorti ingress day-grade misclassification measured on declared synthetic fixtures (0/4 and 2/2); **real error rate [U] NOT_RUN** — no production-data run was authorized. Kota PRESERVE is record-only: w25 unwired; M-4 operand audit required before any use.

## Tests

Per-step batteries green; current gochara suite 252 passed (includes the 5.1–5.3 tests).

## Unsure of

- The real moorti misclassification rate remains unknown by design ([U]); the synthetic fixtures bound the mechanism, not the field rate.
- 5.4's Kota record asserts PRESERVE-only; any future wiring of w25 needs the M-4 operand audit first — that precondition is recorded but not enforceable by code here.
