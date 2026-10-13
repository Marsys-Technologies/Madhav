Offline acceptance for J-0c's disposition artifact (standard library; deterministic and read-only).
Run from this directory:
`python3 -B j0_disposition.py check <disposition.json> --inventory-prs <prs.json> --inventory-state <state.json> --repo <working-copy>`
Exit 0: accepted; 1: refused; 3: unreadable/invalid/unpinned input (unknown); 2: CLI usage error.
Stdout on 0/1/3 is one `ky.accept/1` JSON object; all measured semantic violations are reported.
Checks inventory SHA-256 pins, exact rows, coverage counts, row fields, evidence references and phase order.
Also checks named phase/dependency refusals, PR3141's small-test restriction, and reserved-ruling routing.
(I) INTERPRETATION: `coverage.decisions`, `coverage.sealed_decisions`, `coverage.holds` state class totals.
Holds count the global record plus every operational record, including inactive/released records.
Evidence paths: filename-extension tokens, ./ or / paths, or backticked paths (spaces/directories allowed).
Known item IDs in dependencies and explicit PR/#/pull references bind phase checks; same phase is allowed.
Commit IDs are checked for 7–40 hex syntax; commit existence and PR status are not checked.
No network/GitHub calls; evidence persuasiveness belongs to the independent reviewer.
Does not establish independent inventory acceptance, freshness, protected approval or actual terminal state.
See the job's ACCEPT_REPORT.md for obligations needing additional receipts or semantics.
