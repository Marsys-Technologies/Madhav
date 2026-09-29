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
