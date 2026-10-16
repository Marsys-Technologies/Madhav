---
artifact: KR1_TARANGA_KERNEL_TEST_ARCHIVE
version: "1.0"
status: ARCHIVED
produced_on: 2026-10-16
---

# Retired Taraṅga kernel tests

KR-1 pre-build archives these two suites unchanged. Immediately before retirement,
both suites passed: 44 tests. Their `.py.txt` suffix preserves the original source
without collecting imports of the deleted package. Git retains the three retired
`services/taranga_kernel` modules at the parent revision.

Replacement: `platform/python-sidecar/pipeline/orchestrator/writers/ka_taranga.py`
(K6-4) projects monthly field integrals. Its active tests are
`tests/l3/ka_taranga/test_contract.py` and `tests/l3/kala_db/ka_taranga/test_monthly.py`.
Harmonic means, the old planet-domain roster, and NBRY timing weights are not
asserted to be equivalent to the replacement's integral estimand.

(I) INTERPRETATION: retire the unused kernel separately from `taranga_service`.
No active production module imports the kernel. The HTTP router still imports
`taranga_service`, so that service remains pending its real reader migration.
Alternative: retain both until the HTTP replacement exists. This branch still
waits for the campaign's K9-6 landing gate; it activates nothing.

| Original path | Archived path | SHA-256 of original bytes |
|---|---|---|
| `platform/python-sidecar/tests/l3/test_taranga_kernel_extraction.py` | `99_ARCHIVE/kalayantra/kr1/test_taranga_kernel_extraction.py.txt` | `2a26c908d112305dfa772e1f50c498256a8a4e9d207132c392cab244467d5d43` |
| `platform/python-sidecar/tests/l3/test_taranga_promise_formula.py` | `99_ARCHIVE/kalayantra/kr1/test_taranga_promise_formula.py.txt` | `fd691c7b996d0c69481672d3e1f26b30daa4e060d37238bdeeffd7277535c9ea` |
