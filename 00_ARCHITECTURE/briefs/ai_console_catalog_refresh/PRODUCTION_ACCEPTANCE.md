---
artifact: AI_CONSOLE_CATALOG_PRODUCTION_ACCEPTANCE
version: 1.0
status: CATALOG_SCOPE_VERIFIED_MAIN_SYNC_PENDING
produced_on: 2026-10-03
authority: Native-approved AI Console production deployment
---

# Corrective production acceptance

This qualifies the catalogue/CLI refresh scope, not the entire AI pipeline. The first rollout was rejected and web traffic
restored to the verified prior revision. That chronology remains in RELEASE_EVIDENCE.md.

## Earned source and bridge gates

- Corrective PR #2985: source `fb600b74e8b4fc788b9e7f6f6c587342067154c7`.
- PR quality run `37067876128` and image build `37067876122` passed.
- Protected merge-group `37069080204` passed. PR merged at 21:59:43 UTC, 2 October,
  to exact main `55a666f8943bcda313f1e9bc52f3ea3d47916c96`.
- Main-push quality run `37070035441` passed. Automatic deployment `37071001730`
  started at that exact SHA; no manual override or protection bypass.
- Reviewed private bridge pair activated after staged/live hash preconditions,
  syntax checks and rollback backup. Existing service is active.
  Server SHA256: `2efab1a95f3a4fc5d9d0c9d6789abde7ed8a374b882c117edaf59379655f2944`.
  Protocol SHA256: `72f27257dd21f42974c21b816609fbae35ec4b2fabc7fcfd9cc1a20db710f5e4`.
  Backup: `/opt/marsys-ai-cli-bridge/backups/catalog-correction-fb600b74e-20261003`.
- Authenticated native metadata endpoints on the existing private interface all
  returned 200: Codex 7 models/7 effort-bearing; Claude 12/11; AGY 14/0; Kimi Code 4/0.
  A first diagnostic used loopback although this service intentionally binds its
  private interface; the corrected private-interface client passed. No service
  exposure, network/IAM change or inference was involved in these metadata calls.
- Applied migration 1301 source hash remains unchanged:
  `5d010201d9c8eebe4476634cd2f2b5693e04b413440611ace62ddd93f8b4602f`.
- Parent final suite: 15,099 passed, 975 skipped, two todo; TypeScript zero errors;
  full lint zero errors/595 existing warnings; 22 guarded disposable-DB tests passed.
  Disposable test container stopped, not deleted. Production data was not copied.

## Earned live gates

- Automatic deployment `37071001730` succeeded. Exact served revision
  `amjis-web-probe-55a666f8943b-37071001730-1` has the main commit label and 100%
  traffic; public health returned OK. Routine isolation and migration jobs passed;
  bootstrap/protected public-schema mutations and unrelated service builds were skipped.
- Fresh authenticated production entry refreshed Codex 7, Claude 12, AGY 14 and
  Kimi Code 4 named choices, plus retained Built-in defaults where validated.
  Installed versions: 0.158.0, 2.1.284, 1.2.15 and 2.1.1 respectively.
- OpenAI refreshed 52 catalog models, Gemini 20 and OpenRouter 401. Gemini's manual
  refresh icon also completed at 04:06:02 IST. These are discovery counts, not
  claims that every model can generate for this account. No paid API test was run.
- OpenAI Manage models opened the shortlist by default. Full catalog and search
  narrowed to the single GPT-6-Astra entry. The charge acknowledgement was left
  unchecked and Test and add was not invoked; the dialog was closed without change.
- In unsaved Codex drafts, every role could select GPT-6-Astra and offered model
  default plus low/medium/high/xhigh/max/ultra. In unsaved Claude drafts every role
  could select Sonnet 4.6 and offered model default plus low/medium/high/max;
  individual Claude setups contained only its own models, no Gemini or GPT choices.
- An explicit mixed CLI draft selected Claude/Sonnet for synthesis, Codex/GPT-6-Astra
  for planning, and AGY/Flash Low for deep planning. Both Claude and Codex effort
  could be selected as Low; AGY correctly offered disabled Model default only
  because its catalog does not advertise a separate effort control. All drafts
  were cancelled, not saved. The current Claude Code Built-in default was unchanged.
- Explicit production AGY Test local CLI returned HTTP 200 at 22:34:17 UTC
  (22.595 seconds); the page changed to Reachable, last checked 04:04:38 IST, and
  enabled four-role setup with all 14 named choices plus validated Built-in default.
  The earlier native Flash-low proof and this web validation are subscription-only,
  not API-key inference or a complete Pariprasna-turn proof.
- Manual AGY metadata refresh completed at 04:06:58 IST, retained Reachable and the
  verified installation, and cleared the earlier page-local test-required hint.
- Screenshot of populated production Codex role controls saved at
  `/tmp/ai-console-production-codex-roles-20261003.jpg`.

## Independent live qualification

- Independent verifier completed the bounded 22:28–22:43 UTC observation at
  22:43:36 UTC: 66 requests (58 HTTP 200, two redirects, four cron-authentication
  401s and two non-AI-route 404s). All 32 AI Console requests were HTTP 200;
  zero HTTP 5xx and zero severity-ERROR entries. Health remained 200 and the
  corrected revision continued serving 100% traffic. Unrelated non-AI errors are
  not relabeled as successful checks or repaired by this work order.
- Independent final bridge recheck matched both hashes, active service, same
  loaded user and command. The migration 1301 source remained immutable.
- PR #2982 advanced main to `b4c4b89fd7d4e6fc8c80b7e008a3542a29a2f0e8` during
  qualification. Its 14 governance/census paths do not alter AI Console, bridge
  or migration 1301. Automatic successor deployment `37073733578` is running;
  latest-main synchronization is pending and is not inferred from the earlier watch.
- Separate Pariprasna behaviour smoke `37073866301` failed the real authenticated
  synthetic-chart turn step. Its assertion self-test passed. This release's
  catalogue qualification does not certify that pipeline or repair this failure.

The owned correction lease was released with this catalogue-only outcome and
verified on remote coordination commit
`25b3fd847c8a1d7f75f5ad207e57a69fc92c3f7c`. This is not a claim that the unrelated
successor deployment finished. No further owned runtime mutation is planned.

Remaining administrative gates: successor deployment synchronization, governed
closure emission/validation and protected integration of final evidence.

## Residual UX observation

The page-local AGY refresh hint saying to run a test remained after the successful
test, despite the card becoming Reachable and role setup being enabled. A manual
refresh cleared that prior hint. This transient feedback inconsistency is booked
as AI-CONSOLE-CATALOG-UX-HINT; no saved readiness/model/role/default was falsified.

No paid API generation was used for these release/correction checks. Native CLI
usage is not API-key billing reconciliation. Existing Anthropic attention state,
historical untested API selections/custom configuration repair and retired direct
Kimi connection remain unchanged. No saved key, role configuration or default was
changed. This release does not certify every catalogue model or a full Pariprasna turn.
