# MARSYS-JIS private AI CLI bridge

This service exposes only the four registered CLI operations to the production web service over the
Google Cloud private network. It does not accept executable paths, shell commands, user IDs, or
arbitrary argument lists.

The production web service must keep `MARSYS_AI_LOCAL_CLI_EXECUTION_ENABLED=false`. Remote access is
enabled separately with `MARSYS_AI_CLI_BRIDGE_URL` and the versioned `MARSYS_AI_CLI_BRIDGE_TOKEN`
secret. The VM service reads the same token from `/etc/marsys-ai-cli-bridge/token`.

Network access is limited twice: a VM firewall allow rule accepts TCP 8787 only from Cloud Run
revisions carrying the `amjis-web-cli-egress` network tag, and a higher-priority deny rule blocks all
other sources. The server also binds only to the VM's internal address and requires the bearer token.

## Catalog refresh deployment

Ship `server.mjs` **and** `catalog-protocol.mjs` from the same reviewed commit to
`/opt/marsys-ai-cli-bridge/`. The server imports the protocol module at startup;
copying only the server will prevent the service from starting. Preserve a paired
backup of both files before replacing them, then restart the existing service and
verify its private health endpoint. Rollback restores the pair together.

Refresh inspects the configured execution host (this VM in production, not the
developer's Mac). It checks the installed version and subscription authentication,
then requests model/effort metadata without sending a generation prompt. It does
not install or upgrade the CLI. A new binary/version must pass the separate
explicit CLI execution test before it becomes usable for roles. API model refresh
also performs discovery only; it does not create individual model-test evidence.
During the additive rollout, historical reachable installations with no stored
fingerprint preserve readiness at the same detected version. Refresh does not
invent a verified fingerprint or warm their execution cache; the existing cold-start
execution revalidation or explicit CLI test establishes it.

The UI refreshes stale catalogs on entry (15-minute successful freshness window)
and offers a per-card refresh icon. Server-side leases and a one-minute cooldown
bound concurrent/manual refreshes. A failed refresh retains the previous catalog
and saved role assignments, while showing the failure and last successful refresh.
