# AI Console catalogue release — 3 October 2026

Status: FIRST RELEASE FAILED LIVE ACCEPTANCE AND WAS ROLLED BACK; NARROW CORRECTION IN PROGRESS. This record is not a deployment-completion claim.

The first checklist records the initial preflight snapshot; subsequent verified progress below supersedes its staged/pending descriptions.

- Native explicitly requested stopping the isolated preview and deploying to production.
- Local Next server and disposable preview database are stopped. Production data was never copied into the preview.
- PR #2977 rebased cleanly on `0bf602f33afbe2ad4a345ad0b5173a90ff0491d3`; source head `50b7729c6c20f9b73127142e27f762e91718a66a`. All refreshed PR checks green. Local TypeScript and migration guard passed; 954 focused tests passed, 37 skipped.
- Release lease `MADHAV-AI-CONSOLE-CATALOG-RELEASE-20261003` claimed and remote verified at `58621d8a3d41635bf14b1f157e48e0da4dd484f0`; expiry 04:50 IST. Suvarna tracker and Gochara 4.0 plan review chats acknowledged the hold on new releases; existing jobs are not cancelled.
- Predecessor deployment `37052101597` succeeded. Successor `37053610030` succeeded. Automatic duplicate `37054842178` at the same `0bf602f33` SHA is still running; no bridge service activation or protected PR merge until it completes successfully.
- Fresh production Cloud SQL backup `1790969348793` succeeded at `2026-10-02T19:30:50Z` (01:00:50 IST, 3 October).
- VM `marsys-jis-ai-cli`, zone `asia-south1-b`: current bridge active, Node 18.19.1, Codex 0.158.0, Claude Code 2.1.284. Access uses IAP; no network/IAM or CLI upgrade performed.
- Current bridge SHA256 `b7ea4e3ee87629f452ae0c6ab062da28793386582091f6db5ab6d48fa175308b` equals current-main source. No existing protocol module in the live directory.
- Reviewed files staged only in VM `/tmp`: server SHA256 `90d739ec5ea8335fc3cec6f7aab1773f81c19858d57ab77d1fd5e1142a44fb5c`; protocol SHA256 `72f27257dd21f42974c21b816609fbae35ec4b2fabc7fcfd9cc1a20db710f5e4`.
- Native metadata-only discovery using the staged protocol under the VM service user succeeded: Codex seven models with exact per-model efforts; Claude twelve model choices with advertised effort support. Codex account type was ChatGPT; Claude auth was claude.ai/firstParty. No prompt/turn/generation request, API-key environment, persistent login or configuration change was used.
- Authenticated production AI Console baseline observed: Claude Code Built-in default; Codex/Claude reachable but only Built-in default in the old UI; no custom CLI configuration. No saved choice/default changed. Anthropic remains Needs attention and was not retested with a paid probe.
- Web ERROR baseline since 19:20 UTC: zero log timestamps returned. This is not a successful AI-turn or cost-reconciliation claim.
- Legacy local proxy database authentication failed read-only with 28P01. No data inference or credential recovery followed. Production migration verification must use the protected deployment runner and live application evidence.

## Subsequent verified progress

- An unrelated main merge, PR #2945, reached `75dbfd2bc399ef38d4737828562ffa81cf29fce9` at 19:57:14 UTC despite the 19:49:22 coordination hold request. Its automatic deployment `37058670539` is in flight. No cancellation or foreign-source edit was performed.
- Source rebased cleanly on that main; current source head `429fe00bbd59a92502179e1d498342e16a166988`. TypeScript and 954 focused tests (37 skipped) passed again; refreshed CI is pending.
- Paired bridge activation completed with staged-file and old-live-file SHA preconditions, syntax checks, rollback backup, installation and existing-service restart. Service is active. Backup `/opt/marsys-ai-cli-bridge/backups/catalog-refresh-50b7729c6-20261003/server.mjs` has the verified old SHA; protocol module was previously absent.
- Authenticated private HTTP catalog endpoints all returned 200: Codex 7 models/7 effort-bearing models; Claude 12/11; Antigravity 14/0; Kimi Code 4/0. Providers not advertising effort levels must show Model default, not fabricated levels. A first diagnostic client incorrectly expected stdout instead of the documented models response; the corrected client passed, with no product change required.
- Restart reported a pre-existing unit-on-disk change warning. No daemon reload or unit modification was performed; the existing loaded service user/ExecStart matched the intended bridge and all private endpoints passed.
- Two bounded, direct-bridge subscription execution smokes passed (HTTP 200, exact OK): Codex `gpt-6-astra` with low effort, Claude `sonnet` with low effort. Tools and persistence were disabled. These bypass the web pipeline/usage ledger and are NOT Pariprasna or cost-reconciliation acceptance. No API-key environment or API fallback route exists in these direct calls.
- Actual CLI usage, not a tiny-input claim: Codex 14,125 input (12,288 cached), 5 output, 0 reasoning-output; Claude 2 input plus 2,031 cache-creation and 535 cache-read input, 4 output, 0 thinking-output. Native preambles account for more input than the short prompt. This is subscription usage, not paid API-key generation evidence.

Pending: protected merge after current-main gates and predecessor deployment; migration 1301 application/hash proof; exact served web SHA and traffic; authenticated refresh/dropdown/effort inspection; post-release error observation and lease release. Rollback retains the old bridge file and previous web revision; additive migration data should not be destructively reversed.

## Protected queue handoff

- Predecessor `37058670539` completed successfully; deployment queue was empty before submitting this release. Pre-release 100% web traffic is on `amjis-web-probe-75dbfd2bc399-37058670539-1`, retained as a rollback target.
- All refreshed PR checks at source head `429fe00bbd59a92502179e1d498342e16a166988` passed, including the current-main C23 checks and web build. Main remained `75dbfd2bc399ef38d4737828562ffa81cf29fce9`; no migration 1301 file exists on that main.
- PR #2977 submitted through the protected merge queue with an exact source-head precondition. Merge-group run `37061147758`, temporary head `411c0549195ec761303133c36900fc8a0b66b138`, is running; no protection bypass or admin merge used.
- Coordination progress update `4cfed5d9ad9b18c2d5730a05f33863ef1f3465a7` pushed and verified remotely. A first push failed without advancing remote; the normal retry succeeded on the unchanged parent.
- Protected merge-group CI `37061147758` passed. PR #2977 merged at `2026-10-02T20:43:34Z` to exact main SHA `411c0549195ec761303133c36900fc8a0b66b138`; remote main verified. Main-push CI `37062416003` is running, after which automatic production deployment must qualify the web and migration.
- Main-push CI `37062416003` subsequently passed. Automatic deployment `37063594799` started at that exact merged SHA, without manual dispatch or override.
- Pre-release HTTP baseline since 20:40 UTC: 10 sampled web requests, zero HTTP 5xx, median 0.0623 seconds and sample p95 0.6102 seconds. This small sample is not a service-wide performance guarantee.
- Routine production migration job `111027391523` passed. Its log attests immutable source SHA `411c0549195ec761303133c36900fc8a0b66b138` and explicitly records `Applied: 1301_ai_console_catalog_refresh.sql` at `2026-10-02T21:06:23.4463070Z`. Exact source-file SHA256 is `5d010201d9c8eebe4476634cd2f2b5693e04b413440611ace62ddd93f8b4602f`; the reviewed transactional runner records this hash on application. The ledger row was not independently queried using a recovered credential.
- Protected ownership/isolation inspection passed; bootstrap and protected public-schema mutation jobs were skipped. Web image build remains pending; other service images are not selected by this release.

## Failed live acceptance and verified rollback

- Deployment `37063594799` completed successfully and served exact main `411c0549195ec761303133c36900fc8a0b66b138` at 100% traffic on `amjis-web-probe-411c0549195e-37063594799-1`. Public health returned OK. These were deployment signals, not feature acceptance.
- Authenticated live inspection found Codex seven named models plus Built-in default and Claude twelve named choices plus Built-in default, with model-specific effort metadata. OpenAI metadata refresh succeeded with 52 models. Gemini and OpenRouter refresh each returned HTTP 500 at 21:14:15 and 21:14:17 UTC. The 15-minute qualification watch therefore failed; it was not a green release.
- Installed AGY now reports 1.2.15. The exact approved 1.2.12/1.2.13 application and bridge pins rejected it before inference, leaving Needs attention. No unsupported version was silently accepted.
- Web traffic was explicitly reverted to the previously verified `amjis-web-probe-75dbfd2bc399-37058670539-1`, with 100% traffic verified. The backward-compatible paired bridge remains active; additive migration 1301 remains applied and must not be edited or destructively reversed. Keys, saved role choices, and user default were not changed.
- The original release lease was released with failed-acceptance/rollback status. A fresh correction lease `MADHAV-AI-CONSOLE-CATALOG-CORRECTION-20261003` was pushed and remotely verified at coordination commit `5390d61401be6784eba590099690d38da2f66d42`, start 02:50 IST, expiry 06:50 IST on 3 October. The correction scope is provider discovery-to-persistence validation and an independently proven exact AGY 1.2.15 compatibility extension only.
- Regression-first reproduction used real Google/OpenRouter adapters and real strict repository validation, substituting only external HTTP and PostgreSQL transport. Both realistic capacity-metadata fixtures failed before the fix with unrecognized `contextWindow`/`outputLimit`; 17 existing cases passed. Explicitly projecting the persistence contract, without weakening the strict DAO or changing migration 1301, made all 19 cases pass.
- Broader checks, disposable-database proof, independent review, protected correction merge/deployment, authenticated live recheck, fresh observation watch, and final lease release are still pending.
