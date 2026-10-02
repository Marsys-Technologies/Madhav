# Catalogue release correction — source verification

Status: source review and corrected production catalogue qualification passed; final synchronization/close evidence in PRODUCTION_ACCEPTANCE.md.

The first release was merged and deployed, but authenticated acceptance found two
API catalogue-refresh HTTP 500 responses. Traffic was restored to the previously
verified web revision. Applied additive migration 1301 remains immutable.

## Reproduction and fix

Real Google/OpenRouter discovery adapters return capacity fields alongside model
capabilities. The strict persistence contract intentionally has no capacity fields.
Regression fixtures exercised those real adapters and real DAO validation, replacing
only HTTP and database transport. Before the fix, both failed with unrecognized
`contextWindow` and `outputLimit`; 17 existing cases passed. After explicit field
projection at the refresh service, all 19 passed. Strict validation remains intact;
advertised effort values and explicit null defaults survive projection.

AGY on the private execution VM reports 1.2.15, outside the prior exact pins. One
bounded native headless subscription-protocol check under the existing service user
returned SUCCESS and exactly OK. The native consumer Google OAuth scheme was
inspected without emitting credential values; no saved direct API key, API-key
environment, API-key flag or application API fallback was used. Reported CLI usage
was 13,330 input and one output token. This is not web-pipeline/billing acceptance.
The app, bridge and smoke script now admit exactly 1.2.12, 1.2.13 and 1.2.15. Unknown
versions remain blocked; no CLI binary, authentication or installation changed.

## Independent red-team

The independent reviewer inspected the combined projection, realistic fixtures,
exact-version admission and real private-bridge metadata fixture. Verdict: PASS,
no blocker. Its fresh run passed 44 tests across five focused files. It confirmed
strict DAO preservation, omitted versus empty effort semantics, explicit null
default preservation, consistent exact pins, rejection before discovery for an
uninspected version, and absence of migration/credential/role/default/API-generation
changes. Optional hostile-extra-field and empty-effort fixtures are follow-up test
strengthening, not unresolved correctness blockers.

The CLI specialist independently ran 113 focused tests, targeted lint and both
script syntax checks. The parent fresh complete suite passed 15,099 tests, with
975 skipped and two todo. Disposable guarded localhost PostgreSQL passed all 22
real catalogue/isolation tests; generated schemas were removed by test cleanup.
Full lint found zero errors and 595 pre-existing warnings. A new fixture-only
missing NODE_ENV field was repaired by adding the literal test environment to the
intentionally stripped child environment, without copying host secrets. Both the
specialist and parent fresh complete TypeScript checks then passed; the parent's
fresh four-file correction recheck passed all 30 tests.

## Deployment-gate snapshot before rollout (historical)

- Protected PR/build/merge-group/main gates.
- Paired private bridge activation with exact-file preconditions and backup.
- Exact served web SHA/traffic, authenticated Gemini/OpenRouter refresh and native
  CLI model/effort inspection, safe unsaved role-setup inspection.
- Explicit AGY installation test against the updated bridge (subscription only).
- Fresh 15-minute error observation; saved roles/default remain unchanged.
- Verified remote lease release and governed session close.

No paid API generation was used for these release/correction checks. This does not
state a token total for the entire historical conversation or successful Pariprasna
execution. Existing unrelated account/setup issues are not marked repaired here.

Protected integration and corrective deployment subsequently passed at main
`55a666f8943bcda313f1e9bc52f3ea3d47916c96`. Authenticated UI checks and the independent
15-minute catalogue qualification passed. `PRODUCTION_ACCEPTANCE.md` records the
actual live gates, successor-main deployment state and remaining boundaries;
this source-review record does not assert full Pariprasna turn or billing proof.
