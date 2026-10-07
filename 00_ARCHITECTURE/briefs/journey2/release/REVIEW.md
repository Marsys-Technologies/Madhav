---
artifact: JOURNEY2_RELEASE_REVIEW
version: 1.3
status: PASS_WITH_FIXES
---

# Independent application review and cadence red-team

Required independent code reviewer `/root/journey2_release_review` inspected base `1e5d1b8945a0eda08b290abc5d30c5aa564e37fd` to frozen head `8117eb8173fac2d4199fc6b3ae13e4ec25ed583a`, plus related DAL/callers and governed release records. Static review did not rerun tests or certify production/provider execution. Initial verdict: no Critical findings; three Important/MED findings; not ready to merge.

| Finding | Correction | Actual regression |
|---|---|---|
| UI allowed receipt-less durable answers but restoration/history/tag SQL still rejected them | Persisted assistant eligibility across backend GET/history/answer and conversation tags; retain owned consume thread, active current chart access and archive guards | Remove receipt key entirely; real SQL GET, exact legacy answer forwarding, both PATCH scopes, history plus user-answer/foreign/archive rejection |
| Selected share title could disclose an excluded earlier question | Generic selected-answer title in public reader and private print; selected MD/JSON contain only scoped exchange | Sensitive first-question title excluded when sharing/exporting later answer |
| Review confirmation retry attempted an illegal open-to-confirmed transition | Check lifecycle under parent ledger row lock; return for accepted states without recomputing stamp or modifying settled confidence; reject dismissed/lapsed/stale | Repeat review action and stream-then-review preserve complete saved row; closed row stays closed; rejected states stay rejected |

Root verification after corrections: 24/24 dedicated disposable PostgreSQL checks pass, TypeScript and changed-file ESLint have zero errors. Full reconciled-main unit suite before these corrections: 15,860 passed, 1,088 skipped, 2 TODO; 1,452 passing files, 110 skipped. Corrective head must receive final independent review and refreshed rendered print proof before protected merge.

Cadence inspection covered integrity, accuracy, consistency, scope, governance, security, authority and evidence fidelity. Source-answer provenance, server-captured claims, atomic rollback, immutable settled claims, ownership/current entitlement and narrowly anonymous sharing were traced. No new Jyotish computation, layer writer, asset identity, credential/permission change or learning ratification was identified. Inspection obligation performed; final corrective verdict and common close remain open.

Declined claims: production migration application/locks, serving SHA/traffic, real provider/engine qualification, learning completion and external digest delivery. Learning sink remains explicitly parked and digest transport log-only. Synthetic browser and disposable SQL proof do not establish live outcome acceptance.


## Final independent verdict

Immutable re-review at `8ce6c9594f96cc946c9c249555144fe4453f78aa`: ready to merge from code/security review, subject to required protected checks and refreshed print evidence. No remaining HIGH/MED findings. Cadence verdict PASS_WITH_FIXES. The re-review additionally caught a nested pool checkout introduced by the first correction; resolved by routing source provenance through the transaction executor and computing scripted fallback before checkout. A real max:1 pool with 300ms checkout bound confirms and retries successfully. Dedicated PostgreSQL checks now25 passed.

Rendered corrective browser proof subsequently passed4 groups at1440x1000 and390x844. Actual Next anonymous public reading/print checks now assert the generic answer title and exclude the sensitive thread title; the synthetic HTTP component host restores/tags/shares an answer with metadata receipt absent. Build used print source identical to frozen8ce; final source build/check receipts remain separate. Evidence: `verification_artifacts/journey2-release/browser/results.json` and PDFs/screenshots. No production/provider claim is implied.


## Accepted-main reconciliation review (7 October2026)

Independent reviewer journey2_release_review: LGTM at38e9199491c2c18296aa8bbfd39aee218b63a43e, ready to merge subject to green protected checks. No actionable HIGH/MED findings. All40 previously reviewed source/migration paths equal8ce6c959 exactly; all14 incoming foreign source/migration paths equal accepted f6fc10bf2, including1323. Accepted foreignCCD027 is byte-preserved; never-main Journey Two authority assigned next freeCCD028 without semantic change. All other manifest entries equal accepted main; register hash, count and root digest valid. Ordinary predecessor must apply1323 before this deployment. Prior application/cadence PASS_WITH_FIXES remains valid. Reviewer did not rerun suites or certify production/provider acceptance.

- 1.2: independent exact reconciliation verdict appended; original application review preserved.


## Original saved-date correction review

Draft review correctly identified unsupported visible-timestamp print parity and omitted Markdown dates. The bounded five-path source correction is PR #3235, basefe224b3a7f7ef1df98f2372b5a92fee8d1adb509. First immutable headf8d307a006e90b19f244abe281f63510ad3bfabf review found MED PostgreSQL microsecond truncation and LOW impossible-date normalization. Both were fixed before admission to the protected queue. Actual SQL now uses six-digit fractions across JSON, Markdown and private/public ReadingView; helper regressions cover timezone offsets, leap dates, impossible calendar/clock values and no invented export time.

Final independent head108bb09018859ac3b506190939cbc682abcfbc38 verdict: LGTM, no remaining HIGH/MED/actionable LOW. Ready to merge conditional on exact-head full unit, build, rendered browser and protected checks. The exact-head unit rerun subsequently passed15,881 tests,1,093skipped,2TODO; full ESLint0errors/635inherited warnings, final corrective-path ESLint0warnings and TypeScript0errors. Build and actual SQL-backed Next public reader/print rendering subsequently passed, including full .123456 precision at390x844 without overflow. Private/public server rendering assertions pass against actual SQL. Protected checks remain in progress; native Save PDF needs the locked Mac unlocked. No migration or production acceptance certification.

- 1.3: saved-date draft gap, two first-review corrections and exact final-source LGTM recorded; final runtime evidence remains separate.
