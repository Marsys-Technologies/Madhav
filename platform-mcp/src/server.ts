/**
 * server.ts — MARSYS-JIS MCP HTTP/SSE server entry point.
 *
 * CLEAN SLATE — legacy-teardown (feature/legacy-teardown).
 * All tool registrations stripped. 0 tools registered.
 * Serves: auth + transport + health only.
 * Rebuild tools per layer during the Layer-0 → Layer-3 arc.
 *
 * Architecture: thin HTTP adapter over the MARSYS platform.
 * - Each POST /mcp request creates a new stateless McpServer + transport.
 * - Auth: Bearer key validated via /api/mcp/keys/validate before tool dispatch.
 * - Stateless per D10 (no conversation history; host chat owns the thread).
 * - Cloud Run configuration (amjis-mcp service):
 *   Memory: 512 MB, Min instances: 1, Concurrency: 80, Region: asia-south1.
 *   Health check: GET /health → 200 { status: "ok", service: "marsys-mcp" }
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js'
import express from 'express'
import cookieParser from 'cookie-parser'
import type { Request, Response } from 'express'
import { validateMcpKeyFromHeader } from './auth.js'
import { resolveAuthHeader } from './lib/auth_url_token.js'
import type { Principal } from './types.js'
// M8: structured logging + request-ID + in-process rate limiting
import { generateRequestId, log, logError } from './lib/logger.js'
import { checkMcpRateLimit } from './lib/rate_limiter.js'
// RATE-07: fleet-wide, Postgres-backed, fail-closed gate for the OAuth mutation
// endpoints. NOT a replacement for checkMcpRateLimit above (which still guards
// the authenticated POST /mcp tool path) — a different limiter with a different
// contract; see lib/oauth_rate_limit.ts's header for the side-by-side.
import { oauthRateLimit, chargeValidatedSubject } from './lib/oauth_rate_limit.js'
// M6: surface spec for per-model declared profile
import { callPlatformSurfaceSpec } from './client.js'
// M5: DB-backed OAuth 2.0 endpoints
import { handleAuthorize, handleCallback } from './oauth/authorize.js'
import { handleToken } from './oauth/token.js'
import { handleOAuthDiscovery, handleOpenIDConfiguration } from './oauth/discovery.js'
import { validateAccessToken } from './oauth/token_store.js'
import { registerOAuthClient, validateOAuthClient } from './oauth/oauth_platform_client.js'
import { isRegistrableRedirectUri } from './oauth/redirect_uri_policy.js'
// W5 L2: per-family MCP surface profiles (full/compact≤20/consult), OAuth-scope-gated.
import { resolveMcpProfile, applyProfileGate, type ToolRegisteringServer } from './lib/mcp_profile.js'
import { applyDeprecatedToolGate } from './lib/deprecated_tool_gate.js'
// ŚODHANA T4 (MC-024): portal-wide unknown-param rejection — see file banner for the
// exclusion-by-name list (other builders' territory + PV-locked files) and why a monkeypatch
// (same pattern as the two gates above) rather than ~150 individual call-site edits.
import { applyStrictSchemaGate, type StrictSchemaGateServer } from './lib/strict_tool_schema_gate.js'
// R5 W0a punch-list (#8, 401 headers): every 401 this server returns for a
// client-facing Bearer/OAuth auth failure must carry a WWW-Authenticate
// challenge per RFC 6750 §3 (bare 401s with no challenge header are non-
// compliant and leave MCP clients with no signal to re-auth vs. give up).
// This does NOT build full RFC 9728 protected-resource-metadata discovery —
// that is explicitly routed to the MCP-elevation workstream, not R5 (design
// doc §32 "OAuth/OIDC alignment ... Routes to the MCP-elevation workstream,
// not R5"). It DOES point at the discovery endpoint this server already
// serves (/mcp/.well-known/oauth-authorization-server) so compliant clients
// have somewhere real to go.
function sendUnauthorized(
  res: Response,
  body: { error: string; message?: string; error_description?: string },
): void {
  res.setHeader(
    'WWW-Authenticate',
    `Bearer realm="marsys-mcp", error="invalid_token", ` +
      `error_description="${(body.message ?? body.error_description ?? 'Unauthorized').replace(/"/g, "'")}", ` +
      `resource_metadata="/mcp/.well-known/oauth-authorization-server"`,
  )
  res.status(401).json(body)
}
import { registerMitigationMapTool } from './tools/phala_mitigation_map.js'
import { registerPhalaOutlookTool } from './tools/phala_outlook.js'
import { registerMuhurtaFinder } from './tools/muhurta_finder.js'
// KEYSTONE (M6+M7): mimamsa_lel_intake migrated to callPlatformPrimitive('lel_query').
import { registerMimamsaLelIntakeTool } from './tools/mimamsa_lel_intake.js'
// DOCTRINE-WAVES D-4b Lane B-5 (= BRIEF_D4.md v2.0 Lane C-6): mechanism_retrodiction
// surface — CONFIRMATION ONLY, never prediction input.
import { registerMechanismRetrodictionTool } from './tools/mechanism_retrodiction.js'
import { registerMimamsaOutcomeTool } from './tools/mimamsa_outcome.js'
// KEYSTONE REQUEST: mimamsa_outcome (record_outcome / mimamsa_calibration) has no registry primitive.
// REQUEST to retrieval fork: expose 'record_outcome' capability in tool_name_bridge.
// Still served via sidecar until the registry primitive lands.
//
// KEYSTONE (M6+M7): holistic_bundle sidecar path (bo_2-8) RETIRED — registry path
// (holistic_bundle_chart_facts via callPlatformPrimitive) is the canonical route.
// import { registerHolisticBundleTool } from './tools/bo_2-8.js'  // RETIRED
import { registerPhalaEventAnchorsTool } from './tools/phala_event_anchors.js'
// KEYSTONE REQUEST: phala_event_anchors (phala_anchors table) has no registry primitive.
// REQUEST to retrieval fork: expose 'phala_event_anchors' capability in tool_name_bridge.
// Still served via sidecar until the registry primitive lands.
import { registerHolisticBundleRetrievalTool } from './tools/retrieval/holistic_bundle.js'
import { registerKalaTemporalRetrievalTool } from './tools/retrieval/kala_temporal.js'
import { registerGocharaWindowsTools } from './tools/retrieval/register_gochara_windows.js'
// KEYSTONE REQUEST: kala_temporal_bundle (KA-3-COMPOSITE: timeline/convergence/obstruction/snapshot)
// has no registry primitive. REQUEST to retrieval fork: expose 'kala_temporal_bundle' capability.
// Still served via sidecar until the registry primitive lands.
// Stream G — L1 Gaṇita PyJHora capabilities (BRAHMA-G-1)
import {
  registerComputeNatalPositionsTool,
  registerQuerySpecialLagnasTool,
} from './tools/retrieval/pyhora_natal.js'
// L0FR Stream A: L0 Brahmagyan pattern-validation capabilities
import { registerL0BrahmagyanTools } from './tools/l0_brahmagyan.js'
// L0FR Stream B: L0 Ephemeris capabilities (ephemeris_daily 1900-2150)
import { registerEphemerisTools } from './tools/l0_ephemeris.js'
// L0FR Stream F: Remedy Corpus retrieval tools
import { registerRemedyTools } from './tools/retrieval/remedy_tools.js'
// SATYA-ŚEṢA W4: L0FR Stream C (brahmagyan.texts) — read_classical_text.ts implements 5
// fully-working MCP tools (backend primitives verified live via tool_name_bridge.ts's
// MCP_TO_RETRIEVAL_TOOL whitelist: read_classical_text/search_classical_texts both resolve
// to marsys://tool/L0/query_classical_texts; read_chapter/list_classical_texts/
// find_verses_about resolve to their own L0 URIs) but the file was never imported here —
// a genuine "registered capability, never wired to MCP" instance of exactly the failure
// class this campaign targets (registered ≠ deployed ≠ callable). Classical-text citation
// lookup is consumer-facing truth grounding (B.3 derivation-ledger citations), not an
// internal/consult-only surface — it belongs on the live MCP tool list.
import {
  registerReadClassicalText,
  registerReadChapter,
  registerListClassicalTexts,
  registerFindVersesAbout,
  registerSearchClassicalTexts,
} from './tools/read_classical_text.js'
// D7 — Registry bridge: consolidated workflow tools from the retrieval registry
import { registerRegistryBridgeTools } from './tools/registry_bridge.js'
// BA-P1 — Beyond-Acharya P1 new tool registrations (Groups 1-3 + Phase-1 naming aliases)
import { registerP1GanitaTools }    from './tools/register_p1_ganita.js'
import { registerP1ReferenceTools } from './tools/register_p1_reference.js'
import { registerP1SynthesisTools } from './tools/register_p1_synthesis.js'
import { registerP1AliasTools }     from './tools/register_p1_aliases.js'
// D-1.5b Lane B-7 — B8 derived view: ganita_dasha_lord_capability_get
import { registerP2DashaLordTools } from './tools/register_p2_dasha_lord.js'
// D-2 Lane V-3: two-pass SCAN/FETCH channel over the large signals surface (ledger row 20)
import { registerScanFetchTool } from './tools/scan_fetch_signals.js'
// D-2 Lane V-3: per-chart verified reading-notes (CR-38/71/80), ledger row 25
import { registerReadingNotesTool } from './tools/reading_notes.js'
// M2 — Chart selection: list_my_charts + select_chart
import { registerChartSelectionTools } from './tools/chart_selection.js'
// M3+M4 — Session tools: recall_session + list_my_sessions
import { registerSessionTools } from './tools/session_tools.js'
// R5 — Richness Layer: MCP resources (9 registered) + guided-reading prompts
import { registerResources } from './resources/index.js'
import { registerPrompts } from './prompts/index.js'
// D-2 Lane V-2 — Vidhi Engine plan_retrieval meta-tool (+ capability-version staleness kill)
import { registerVidhiPlanTool } from './tools/register_vidhi_plan.js'
// Elevation Campaign v2.1 · Stream γ (PŪRṆA) · Lane Ω5 — dossier: gather-then-compose paging
// engine with a structural synthesis gate (NATIVE-RULED-001, scoped server.ts exception —
// registerDossierTool itself lives in tools/dossier.ts, γ's own file; this import+registration
// is the sole change server.ts needed).
import { registerDossierTool } from './tools/dossier.js'
// W6 — prashna_ask: job-handle-first full-loop engine call (Task 7)
import { registerPrashnaAskTool } from './tools/register_prashna_ask.js'
// W6 Part 3 — prashna_status: poll a prashna_ask job's progress/final result
import { registerPrashnaStatusTool } from './tools/register_prashna_status.js'
// EL-13 — mcp_server_info: catalog_version/tools_changed_at + tools/list_changed staleness kill
import { registerServerInfoTool, MCP_SERVER_NAME, MCP_SERVER_VERSION } from './tools/register_server_info.js'

const app = express()
app.use(express.json())
app.use(cookieParser())

// ── OAuth 2.0 endpoints (M5: DB-backed, real Firebase identity) ──────────────
// Per MCP authorization spec + ChatGPT connector requirements
//
// RATE-07 (PARIŚEṢA-V4 GA-2 ruling, 2026-08-21): every one of the five OAuth
// MUTATION endpoints below now carries `oauthRateLimit(<route>)` — a fleet-wide,
// Postgres-backed, fail-closed gate that runs BEFORE the handler, i.e. before any
// auth-code row is written and before any credential is examined. Previously
// these five had no rate limiting whatsoever: the in-process `checkMcpRateLimit`
// Map below is keyed on `key_id`, which OAuth mutations do not carry, and is
// wired only to `POST /mcp`. See `./lib/oauth_rate_limit.ts` for the identity
// derivation and its disclosed X-Forwarded-For ambiguity.
//
// The two `.well-known` discovery routes are deliberately NOT gated: they are
// idempotent static reads that a connector fetches before it can do anything
// else, and limiting them would break discovery for a shared-egress client
// without protecting any mutable state.

app.post('/mcp/oauth/authorize', oauthRateLimit('oauth_authorize'), (req, res) => void handleAuthorize(req, res))
// GET /mcp/oauth/callback — Firebase auth callback (stamps uid onto auth code)
app.get('/mcp/oauth/callback', oauthRateLimit('oauth_callback'), (req, res) => void handleCallback(req, res))
app.post('/mcp/oauth/token', oauthRateLimit('oauth_token'), (req, res) => void handleToken(req, res))
// RATE-07 (security review fix): gated with the 'oauth_token' key, NOT a
// separate 'oauth_refresh' key. This route is a thin alias — it forces
// grant_type=refresh_token and delegates to the very same handleToken that
// POST /mcp/oauth/token serves. Two distinct bucket keys over one underlying
// operation meant a refresh-token guessing attack got the per-IP budget TWICE
// (once via /refresh, once via /token with grant_type=refresh_token). Sharing
// the key makes the advertised limit the real limit.
app.post('/mcp/oauth/refresh', oauthRateLimit('oauth_token'), async (req: Request, res: Response) => {
  // Redirect to token endpoint with grant_type=refresh_token
  req.body.grant_type = 'refresh_token'
  await handleToken(req, res)
})

// M5: Dynamic client registration (RFC 7591 / MCP OAuth spec)
// Writes to mcp_oauth_clients table via platform API.
app.post('/mcp/oauth/register', oauthRateLimit('oauth_register'), async (req: Request, res: Response) => {
  const authHeader = req.headers['authorization']
  // Registration requires a valid Bearer key to identify the registering user.
  const principal = await validateMcpKeyFromHeader(authHeader)
  if (!principal) {
    sendUnauthorized(res, { error: 'Unauthorized', message: 'Bearer key required to register an OAuth client' })
    return
  }

  // RATE-07 layer 2: now — and only now — that the Bearer key has actually been
  // validated, charge a per-principal bucket. Doing this BEFORE validation would
  // let any anonymous caller spend a named user's registration quota by asserting
  // their uid. `chargeValidatedSubject` writes the 429/503 itself when it denies.
  if (!(await chargeValidatedSubject(res, 'oauth_register', 'principal', principal.user_uid))) {
    return
  }

  const body = req.body as { redirect_uris?: string[]; scope?: string }
  if (!Array.isArray(body.redirect_uris) || body.redirect_uris.length === 0) {
    res.status(400).json({ error: 'invalid_client_metadata', error_description: 'redirect_uris required' })
    return
  }

  // SF-004 (PARIŚEṢA-V4): registration-time URI policy — require https:, or
  // http: on a loopback host for dev; reject fragments and wildcards. See
  // SF004_OAUTH_BINDING_CONTRACT_v1_0.md §5. Applied here (the public-facing
  // RFC 7591 entry point) as well as at the platform API route this call
  // proxies to, as defense in depth.
  const badRedirectUri = body.redirect_uris.find(uri => !isRegistrableRedirectUri(uri))
  if (badRedirectUri !== undefined) {
    res.status(400).json({
      error: 'invalid_redirect_uri',
      error_description: 'redirect_uris must be https: (or http: on localhost/127.0.0.1/::1), with no fragment and no wildcard',
    })
    return
  }

  // Validate any registered client_id/secret from body (for test use-case, skip — new registration).
  void validateOAuthClient  // imported for side-channel use; suppress lint

  const scopes = body.scope ? body.scope.split(' ') : undefined
  const result = await registerOAuthClient({
    ownerUid: principal.user_uid,
    redirectUris: body.redirect_uris,
    scopes,
  })

  if (!result) {
    res.status(500).json({ error: 'server_error', error_description: 'Client registration failed' })
    return
  }

  // RFC 7591 response
  res.status(201).json({
    client_id: result.client_id,
    client_secret: result.client_secret,
    redirect_uris: body.redirect_uris,
    grant_types: ['authorization_code', 'client_credentials'],
    response_types: ['code'],
    scope: (scopes ?? ['mcp:tools', 'mcp:resources', 'mcp:prompts']).join(' '),
  })
})

// OAuth discovery metadata (add registration_endpoint per M5)
app.get('/mcp/.well-known/oauth-authorization-server', handleOAuthDiscovery)
app.get('/mcp/.well-known/openid-configuration', handleOpenIDConfiguration)

// ── MCP endpoint (with OAuth token support) ───────────────────────────────────

/**
 * POST /mcp — main MCP protocol endpoint (Streamable HTTP transport).
 *
 * Each request gets its own McpServer + transport instance, enforcing
 * statelessness (D10: no conversation history; no shared session state).
 */
app.post('/mcp', async (req: Request, res: Response) => {
  // M8: generate a request-scoped trace ID for end-to-end log correlation.
  // Prefer the inbound X-Request-ID from the connector (allows client-side tracing);
  // fall back to a new generated ID.
  const requestId: string =
    (typeof req.headers['x-request-id'] === 'string' ? req.headers['x-request-id'] : undefined) ??
    generateRequestId()
  const requestStart = Date.now()

  // B-MCP-LOG-REDACT (Ruling 64): extracted to lib/auth_url_token.ts so the URL-token
  // fallback's request-framing logic is unit-testable without a live network round-trip.
  const queryKey = typeof req.query['api_key'] === 'string' ? req.query['api_key'] : undefined
  const { authHeader, fromUrlParam } = resolveAuthHeader(req.headers['authorization'], queryKey)

  let principal: Principal | null = await validateMcpKeyFromHeader(authHeader)

  // W5 L2: authKind + OAuth scopes drive the served MCP surface profile (full/compact/
  // consult) — see resolveMcpProfile()'s doc comment. Bearer-key auth (this branch) is
  // this server's own first-party trusted credential → always 'full', set below once
  // authKind is known for certain (after the OAuth branch, which can also set principal).
  let authKind: 'bearer_key' | 'oauth' | null = principal ? 'bearer_key' : null
  let oauthScopes: string[] | undefined

  // M5: also accept OAuth access tokens (DB-backed; survives restart + multi-instance).
  if (!principal && authHeader?.startsWith('Bearer ')) {
    const token = authHeader.slice('Bearer '.length)
    // DB-backed validation via platform API (replaces in-memory validateAccessToken).
    const oauthRecord = await validateAccessToken(token)
    if (oauthRecord) {
      // Fail-closed: never allow 'anonymous' uid through the entitlement gate.
      if (!oauthRecord.uid || oauthRecord.uid === 'anonymous') {
        logError({
          request_id: requestId,
          outcome: 'auth_denied',
          message: 'OAuth token carries no verified uid — rejected',
        })
        sendUnauthorized(res, { error: 'Unauthorized', message: 'OAuth token carries no verified uid' })
        return
      }
      // One identity core (M5.1): OAuth maps to the same Principal shape as Bearer key.
      // Role defaults to 'guest'; super_admin role requires Bearer key with profile lookup.
      principal = {
        user_uid: oauthRecord.uid,
        key_id: 'oauth:' + token.slice(0, 8),
        role: 'guest',
      } satisfies Principal
      authKind = 'oauth'
      // W5 L2: thread the token's granted scopes through to profile resolution — previously
      // discarded here entirely (OT-10's "OAuth scope selects the projection" ruling had no
      // implementation before this lane; every OAuth caller silently got the same unfiltered
      // full tool surface as a first-party Bearer key).
      oauthScopes = oauthRecord.scopes
    }
  }

  if (!principal) {
    logError({
      request_id: requestId,
      outcome: 'auth_denied',
      message: 'Invalid or missing Bearer API key',
    })
    sendUnauthorized(res, { error: 'Unauthorized', message: 'Invalid or missing Bearer API key' })
    return
  }

  // M8: Rate limiting — applied at MCP dispatch level so ALL tools are gated,
  // including sidecar-direct tools that bypass the platform-side limiter.
  const rlResult = checkMcpRateLimit(principal.key_id)
  if (!rlResult.allowed) {
    log({
      level: 'warn',
      request_id: requestId,
      user_uid: principal.user_uid,
      key_id: principal.key_id,
      outcome: 'rate_limited',
      message: 'MCP request rate-limited at sidecar dispatch',
      latency_ms: Date.now() - requestStart,
    })
    res.setHeader('Retry-After', String(rlResult.retry_after_seconds ?? 60))
    res.status(429).json({
      error: 'rate_limit_exceeded',
      message: `Too many requests. Retry after ${rlResult.retry_after_seconds ?? 60} seconds.`,
      retry_after_seconds: rlResult.retry_after_seconds ?? 60,
    })
    return
  }

  // M8: Propagate the request-ID as X-Request-ID on all outbound calls to the platform.
  // The platform receives this and can log it for correlation.
  // We attach it to the response as well so connectors can correlate.
  res.setHeader('X-Request-ID', requestId)

  void fromUrlParam

  // M6: Resolve effective model family.
  // Precedence: x-mcp-model-family header override > per-key binding > 'universal' fallback.
  // The header lets a client override at runtime (e.g. testing a different profile).
  const ALLOWED_FAMILIES = ['anthropic', 'gemini', 'openai', 'deepseek'] as const
  type ModelFamily = typeof ALLOWED_FAMILIES[number]
  const headerFamily = typeof req.headers['x-mcp-model-family'] === 'string'
    ? req.headers['x-mcp-model-family']
    : undefined
  const effectiveFamily: string = (
    (headerFamily && (ALLOWED_FAMILIES as readonly string[]).includes(headerFamily)
      ? headerFamily
      : principal.model_family) ??
    'universal'
  )

  // M6.2: Fetch the surface spec for the effective family.
  // Non-blocking: surface spec is advisory for shaping; failure falls back to serving all tools.
  // Fire-and-forget; surfaceSpec.envelope holds the spec result.
  let responseFormat: 'minimal' | 'standard' | 'detailed' = 'standard'
  try {
    const surfaceResult = await callPlatformSurfaceSpec(effectiveFamily)
    if (surfaceResult.status === 200 && surfaceResult.envelope.ok) {
      const spec = surfaceResult.envelope.result as Record<string, unknown> | null
      if (spec && typeof spec['response_format'] === 'string') {
        const rf = spec['response_format']
        if (rf === 'minimal' || rf === 'standard' || rf === 'detailed') {
          responseFormat = rf
        }
      }
    }
  } catch {
    // Non-fatal: surface spec failure does not block tool serving.
  }

  // Pass effectiveFamily + responseFormat to tools that accept them.
  // Currently stored as request-scoped constants for tool callbacks.
  void effectiveFamily
  void responseFormat

  const server = new McpServer({
    name: MCP_SERVER_NAME,
    version: MCP_SERVER_VERSION,
  })

  // ŚODHANA T4 (MC-024): applied FIRST, before every other gate/registration, so an
  // unknown/misspelled param on ANY tool call (including prashna_ask/prashna_status/
  // mcp_server_info below, which register before the other two gates) is rejected loudly
  // instead of silently dropped. See strict_tool_schema_gate.ts for the exclusion-by-name
  // list (other builders' territory + PV-locked registry_bridge.ts).
  applyStrictSchemaGate(server as unknown as StrictSchemaGateServer)

  // RC-14 breaking flip (MCP_TOOL_NAMING_STANDARD §4 Phase-3): remove the 43 legacy
  // P1 short names from the MCP surface so ONLY the canonical `layer_noun_verb` faces
  // resolve. Applied FIRST (before prashna + the profile gate) and UNCONDITIONALLY
  // for every profile — unlike applyProfileGate, which is a no-op for `full`. Web
  // replay of old persisted names is unaffected (tool_name_bridge, a different door).
  // See lib/deprecated_tool_gate.ts.
  const deprecatedGate = applyDeprecatedToolGate(server as unknown as ToolRegisteringServer)

  // W5 L2: resolve + apply the per-family MCP surface profile (full/compact≤20/consult)
  // BEFORE any register*Tools() call below runs. `applyProfileGate` monkeypatches this
  // request-scoped server's `.tool()` method in place so every existing registration
  // call site (unconditional before this lane) is transparently scoped — see
  // `lib/mcp_profile.ts`'s header for why this is safe-by-construction, not by convention.
  // authKind is always set by this point: the 401 return above already guarantees
  // `principal` (and therefore authKind) is non-null on every path that reaches here.
  const mcpProfile = resolveMcpProfile({ authKind: authKind as 'bearer_key' | 'oauth', oauthScopes })

  // W6 Task 7 — prashna_ask is registered BEFORE applyProfileGate patches
  // server.tool(). It is not part of the retrieval-registry catalog the
  // generated MCP_SURFACE_PROFILES manifest is built from (mcp_profile.ts /
  // src/generated/mcp_surface_profiles.generated.ts, DO-NOT-HAND-EDIT), so the
  // manifest's compact/consult tool_names lists have no entry for it at all —
  // registering it AFTER the gate would silently block it for 'compact' too,
  // not just 'consult' (the requirement is: 'full' and 'compact' MAY call
  // prashna_ask; only 'consult' may not). The tool implements its OWN
  // handler-level entitlement check against the already-resolved `mcpProfile`
  // instead, matching the task's explicit "reject with a clear error inside the
  // handler" design.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerPrashnaAskTool(server as any, principal, mcpProfile)
  // W6 Part 3 — prashna_status is registered alongside prashna_ask, BEFORE the
  // profile gate, for the same reason: it is not part of the retrieval-registry
  // catalog the generated MCP_SURFACE_PROFILES manifest is built from, so
  // registering it after the gate would silently block it for 'compact' too.
  // Polling is harmless for every profile (including 'consult', which could
  // never have produced a job_id in the first place — it just gets the honest
  // "unknown or expired job_id" error), so no handler-level profile gate here.
  registerPrashnaStatusTool(server as unknown as import('./tools/register_prashna_status.js').PrashnaStatusRegisteringServer)

  // EL-13 — mcp_server_info, registered BEFORE applyProfileGate for the same reason as
  // prashna_ask/prashna_status: catalog-staleness detection must be reachable under every MCP
  // surface profile (full/compact/consult), not just whichever ones the generated
  // MCP_SURFACE_PROFILES manifest happens to list it under.
  registerServerInfoTool(server)

  const profileGate = applyProfileGate(server as unknown as ToolRegisteringServer, mcpProfile)

  // L0 Brahmagyan tools (L0FR Stream A pattern-validation capabilities)
  registerL0BrahmagyanTools(server)
  // L0 Ephemeris tools (L0FR Stream B — ephemeris_daily 1900-2150)
  registerEphemerisTools(server)
  // L0 Classical Text tools (L0FR Stream C — brahmagyan.texts). SATYA-ŚEṢA W4 fix: these
  // 5 tools existed fully-implemented since 2026-06-07 but were never registered on the
  // live MCP surface — see the import comment above for the wiring verification.
  registerReadClassicalText(server, () => principal)
  registerReadChapter(server, () => principal)
  registerListClassicalTexts(server, () => principal)
  registerFindVersesAbout(server, () => principal)
  registerSearchClassicalTexts(server, () => principal)

  // L1 Gaṇita — PyJHora natal computation tools (Stream G / BRAHMA-G-1)
  registerComputeNatalPositionsTool(server)    // graha_sthana: 9 planets + Lagna
  // query_dasha_periods REPOINTED to the DB-backed faceted capability (get_dashas) —
  // now registered in registerP1AliasTools so it honors system_id + windows (WP-1.3 b/c,
  // F-0354/F-0471/0485). The old vimshottari-only PyJHora registration is retired.
  registerQuerySpecialLagnasTool(server)       // Lagna + upagrahas (Gulika, Maandi, etc.)

  // L2 Bodha tools
  // KEYSTONE: holistic_bundle sidecar path (bo_2-8) RETIRED.
  // Registry path: holistic_bundle_chart_facts (retrieval/holistic_bundle.ts → callPlatformPrimitive).
  registerHolisticBundleRetrievalTool(server, () => principal)  // chart_facts via registry (L2 Bodha — chart-SCOPED; requires chart_id)
  registerKalaTemporalRetrievalTool(server, principal)    // L3 Kāla composite bundle (chart-SCOPED; CR-40/T-1: now registry-backed, not the dead sidecar path)
  registerGocharaWindowsTools(server, principal)    // D-5 G-4: gochara activation/forecast/election-avoidance views over kala_gochara_windows (chart-SCOPED)
  // L0 Brahmagyan Remedy tools (Stream F — 7 capabilities)
  registerRemedyTools(server, () => principal)
  // L4 Phala tools
  registerPhalaEventAnchorsTool(server, principal)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMitigationMapTool(server as any, principal)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMuhurtaFinder(server as any, () => principal)
  registerPhalaOutlookTool(server, principal)
  // L5 Mīmāṃsā tools
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMimamsaLelIntakeTool(server as any, principal)
  // DOCTRINE-WAVES D-4b Lane B-5: mechanism_retrodiction surface (CONFIRMATION ONLY).
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMechanismRetrodictionTool(server as any, principal)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerMimamsaOutcomeTool(server as any, principal)

  // D7 — Registry-backed consolidated workflow tools (12 MCP tools → registry URIs)
  // These are chart-agnostic: chart_id required on per_chart tools, no default.
  // R5 W0a punch-list (P7): principal threaded through so callPlatformPrimitive
  // (vector_search) can send the 3-header auth pattern instead of the bare
  // internal token that the primitives route was rejecting with 401.
  registerRegistryBridgeTools(server, principal)

  // BA-P1 — New Group-1 computed-chart tools (9), Group-2 reference tools (7), Group-3 synthesis (3)
  // R5.2 A1: principal threaded through so the platform's per-call chart entitlement gate
  // on /api/retrieval/capability (X-MCP-User / X-MCP-Key-Id) can identify the caller.
  registerP1GanitaTools(server, principal)
  registerP1ReferenceTools(server, principal)
  // R5 W0a punch-list (P6): principal threaded through so platformQuery
  // (the four /api/mcp/db/query callers) can satisfy the route's Layer-2 auth.
  registerP1SynthesisTools(server, principal)
  // BA-P1 — Phase-1 naming aliases for all 53 baseline tools (49 aliases; 6 documented deferrals)
  // R5 W2 corpus lane (P7): principal threaded through so callPlatformPrim (used by
  // ref_vector_search + the remedy/lel/calibration aliases) can send the 3-header
  // auth pattern instead of the bare internal token the primitives route rejects.
  registerP1AliasTools(server, principal)
  // D-1.5b Lane B-7 — B8 derived view (ganita_dasha_lord_capability_get)
  registerP2DashaLordTools(server, principal)
  // D-2 Lane V-3: scan_fetch_signals — two-pass channel (SCAN dense index → FETCH-by-id)
  registerScanFetchTool(server, principal)
  // D-2 Lane V-3: reading_notes_get — per-chart verified reading-notes (CR-38/71/80)
  registerReadingNotesTool(server)

  // M2 — Chart selection: list_my_charts + select_chart (2 tools)
  // list_my_charts: entitled chart list by display name; select_chart: validate + return chart_id.
  registerChartSelectionTools(server, principal)

  // M3+M4 — Session tools: recall_session + list_my_sessions (2 tools)
  // recall_session: resume session with entitlement re-check; list_my_sessions: session history.
  registerSessionTools(server, principal)

  // R5 — Richness Layer + WP-1.6: MCP resources (incl. consumption-protocol) +
  // guided-reading prompts (incl. demand_side_chase)
  // M0: principal passed for chart-snapshot gate
  registerResources(server, principal)
  registerPrompts(server, principal)

  // D-2 Lane V-2 — Vidhi Engine plan_retrieval meta-tool (fallback path to a compiled plan;
  // primary path is the vidhi_plan prompt). Serves capability_version + tools/list_changed
  // staleness kill. Registered on this request-scoped server so the staleness notification
  // targets the caller's transport.
  // S-3: principal threaded through so the M0 entitlement gate (remoteAuthorize) can check
  // the caller against the requested chart_id before compiling a plan (GT-35).
  registerVidhiPlanTool(server, principal)

  // Elevation Campaign v2.1 · Stream γ (PŪRṆA) · Lane Ω5 — dossier(domain, chart_id, budget_kb?,
  // cursor?): pages a domain's entire TCI/C7-accounted slice under the C1 budget cap, structurally
  // withholding interpretive surfaces until synthesis_gate reads OPEN. Chart-scoped like the other
  // per-chart tools above; principal threaded through for remoteAuthorize's entitlement check.
  registerDossierTool(server, principal)

  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  })

  // M8: Log request dispatch — captures the tool invocation context.
  //
  // R5 W0a punch-list prerequisite (§31.6 telemetry): this used to log
  // req.body.method verbatim — the JSON-RPC envelope method (e.g. "tools/call",
  // "initialize", "resources/list"), which is the MCP-protocol equivalent of an
  // HTTP verb, NOT the actual tool being invoked. Every tool call was logged
  // identically as "tools/call", making per-tool telemetry (§31.6 call-sequence
  // analysis, all downstream waves) impossible. The real tool name lives at
  // req.body.params.name for "tools/call" requests — extract that; fall back to
  // the envelope method for non-tool-call requests (initialize, list, etc.).
  const rpcBody = req.body as { method?: unknown; params?: { name?: unknown } } | undefined
  const rpcMethod = typeof rpcBody?.method === 'string' ? rpcBody.method : undefined
  const mcpMethod =
    rpcMethod === 'tools/call' && typeof rpcBody?.params?.name === 'string'
      ? rpcBody.params.name
      : rpcMethod
  // W5 L2: fold the resolved profile + any blocked-registration count into the message
  // (rather than widening the shared LogEntry shape for one lane's field) — observability
  // for "which profile served this request" and "did the gate actually block anything."
  log({
    level: 'info',
    request_id: requestId,
    user_uid: principal.user_uid,
    key_id: principal.key_id,
    tool: mcpMethod,
    message:
      `MCP request dispatched (mcp_profile=${mcpProfile}` +
      (profileGate.blockedAttempts.length > 0 ? `, gate_blocked=${profileGate.blockedAttempts.length}` : '') +
      (deprecatedGate.blockedDeprecated.length > 0 ? `, deprecated_blocked=${deprecatedGate.blockedDeprecated.length}` : '') +
      ')',
  })

  try {
    await server.connect(transport)
    await transport.handleRequest(req, res, req.body)
    log({
      level: 'info',
      request_id: requestId,
      user_uid: principal.user_uid,
      key_id: principal.key_id,
      tool: mcpMethod,
      outcome: 'ok',
      latency_ms: Date.now() - requestStart,
      message: 'MCP request completed',
    })
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : String(err)
    logError({
      request_id: requestId,
      user_uid: principal.user_uid,
      key_id: principal.key_id,
      tool: mcpMethod,
      outcome: 'error',
      latency_ms: Date.now() - requestStart,
      message: 'Unhandled error in MCP request',
      error: errMsg,
    })
    if (!res.headersSent) {
      res.status(500).json({ error: 'Internal server error' })
    }
  }
})

// ── GET /mcp — SSE subscription endpoint ─────────────────────────────────────
app.get('/mcp', (_req: Request, res: Response) => {
  res.status(405).json({
    error: 'Method Not Allowed',
    message: 'Use POST /mcp for Streamable HTTP transport (stateless mode). SSE GET not supported.',
  })
})

// ── Health check ──────────────────────────────────────────────────────────────

// Tool count computed from registration calls (BA-P1 recount 2026-07-03 — authoritative):
// ── BASELINE (pre-P1) ──────────────────────────────────────────────────────────
// L0 Brahmagyan pattern-validation (registerL0BrahmagyanTools):  5
// L0 Ephemeris (registerEphemerisTools):                          5
// L1 Stream G PyJHora natal:                                      3
//   (compute_natal_positions + query_dasha_periods + query_special_lagnas)
// L2 Bodha — holistic_bundle_chart_facts (registry path):         1
// L3 Kāla — kala_temporal_bundle (sidecar; registry pending):     1
// L0FR Remedy (registerRemedyTools):                              7
// L4 Phala:                                                       4
//   (phala_event_anchors + mitigation_map + muhurta_finder + phala_outlook)
// L5 Mīmāṃsā:                                                     3
//   (mimamsa_lel_intake [1: lel_query] + mimamsa_outcome [2: record_outcome + query_calibration])
// D7 Registry bridge (registerRegistryBridgeTools):               20
//   D7 workflow tools (12): get_chart_orientation, get_domain_reading, get_signals,
//     traverse_graph, get_positions, get_dashas, get_temporal_windows, get_projections,
//     get_classical_citation, get_remedies, get_chart_quality, list_assets
//   D8 apex tools (8): assess_marriage, assess_career, assess_health, assess_wealth,
//     yoga_activation_by_dasha, get_cgm_subgraph, query_chart_facts, vector_search
// M2 Chart selection (list_my_charts + select_chart):             2
// M3+M4 Session tools (recall_session + list_my_sessions):        2
// ── BASELINE SUBTOTAL: ────────────────────────────────────────────            53
// ── BA-P1 ADDITIONS ───────────────────────────────────────────────────────────
// P1 Group 1 — computed-chart tools (registerP1GanitaTools):      12
//   ganita_strength_get, ganita_structural_get, ganita_condition_get,
//   ganita_sade_sati_get, ganita_tajaka_get, ganita_nakshatra_get,
//   ganita_yogas_get, phala_rectification_get, ganita_transit_anchors_get,
//   ganita_database_schema_get, ganita_concept_locate, ganita_planet_get
//   (last 3: Elevation Campaign v2.1 STREAM α Lane-H — front the batch-1 registry
//   capabilities get_database_schema/concept_locate/query_planet, which existed in the
//   L1_ganita registry index with no MCP-facing tool)
// P1 Group 2 — reference tools (registerP1ReferenceTools):        7
//   ref_rules_search, ref_yogas_get, ref_doshas_get,
//   ref_dignity_reference_get, ref_dasha_systems_get, ref_nakshatra_get,
//   ref_transit_rules_get
// P1 Group 3 — synthesis tools (registerP1SynthesisTools):        3
//   mimamsa_insight_get, bodha_discoveries_get, kala_life_arc_get
// P1 Phase-1 naming aliases (registerP1AliasTools):               45
//   D7/D8 aliases (17): bodha_chart_digest_get, bodha_domain_reading_get,
//     bodha_signals_get, bodha_graph_traverse_get, ganita_positions_get,
//     ganita_dashas_get, kala_windows_get, kala_projections_get,
//     ref_classical_citation_get, bodha_remedies_get, bodha_remedies_search,
//     bodha_quality_get, catalog_assets_list,
//     kala_yoga_activation_get, bodha_graph_subgraph_get,
//     ganita_chart_facts_get, ref_vector_search
//     (apex_marriage/career/health/wealth_assess RETIRED — WP-1.3(i)/LCA-11
//      duplicate-family dedup; capability preserved on canonical assess_* tools)
//   L0 Ephemeris aliases (5): ref_planet_position_get, ref_planet_transit_get,
//     ref_aspects_at_time_get, ref_retrograde_periods_get, ref_ephemeris_year_get
//   L0 Brahmagyan aliases (5): ref_entity_resolve, ref_entities_list,
//     catalog_assets_all, catalog_assets_l0, util_intent_classify
//   L0 Remedy aliases (8): ref_remedies_get, ref_remedies_chart_get,
//     ref_remedies_by_category_list, ref_remedy_get, ref_tantric_remedies_get,
//     ref_remedies_by_planet_get, ref_mantras_get, ref_remedies_search
//   L4 Phala aliases (4): phala_anchors_get, phala_mitigation_get,
//     kala_muhurta_get, phala_outlook_get
//   L5 Mīmāṃsā aliases (3): mimamsa_lel_query, mimamsa_outcome_record,
//     mimamsa_calibration_get
//   L1 PyJHora aliases (3): ganita_natal_positions_compute,
//     ganita_dasha_periods_get, ganita_special_lagnas_get
//   DEFERRED (6): recall_session→session_recall, list_my_sessions→session_list,
//     list_my_charts→catalog_charts_list, select_chart→catalog_chart_select,
//     holistic_bundle_chart_facts→bodha_bundle_get, kala_temporal_bundle→kala_bundle_get
// ── TOTAL (WP-1.3(i) recount 2026-07-12: −4 apex_*_assess retired): ───        117
// D-2 Lane V-2 — +1 plan_retrieval (Vidhi Engine meta-tool):                  +1
// D-2 Lane V-3 — +2 scan_fetch_signals, reading_notes_get:                    +2
// W6 Task 7 — +1 prashna_ask (job-handle-first full-loop engine call):        +1
// W6 Part 3 — +1 prashna_status (poll a prashna_ask job's progress/result):   +1
// RC-14 breaking flip (2026-07-23): −43 legacy P1 short names removed from the live MCP
// surface by applyDeprecatedToolGate (the registrars still CALL server.tool() for them, but
// the gate no-ops those calls — see lib/deprecated_tool_gate.ts). The canonical layer_noun_verb
// faces they duplicated remain. The 6 DEFERRED tools were RENAMED in place (recall_session→
// session_recall, list_my_sessions→session_list, list_my_charts→catalog_charts_list, select_chart
// →catalog_chart_select, holistic_bundle_chart_facts→bodha_bundle_get, kala_temporal_bundle→
// kala_bundle_get) — count-neutral. 122 − 43 = 79.
// CR-24 completion fix (2026-07-24): +1 bodha_mechanisms_get — the CR-24 merge repointed the
// mechanism_read planner primitive's live_tool to bodha_mechanisms_get but never registered the
// corresponding MCP tool (registerP1AliasTools now does, delegating to query_mechanisms.ts).
// 79 + 1 = 80.
// Elevation Campaign v2.1 STREAM α Lane-H (2026-07-25): +3 ganita_database_schema_get,
// ganita_concept_locate, ganita_planet_get — front the 3 batch-1 registry capabilities
// (get_database_schema/concept_locate/query_planet) that existed in the L1_ganita registry
// index with no MCP-facing tool (registerP1GanitaTools now does). 80 + 3 = 83.
// SATYA-ŚEṢA W4 fix (2026-07-25): +5 read_classical_text, read_chapter,
// list_classical_texts, find_verses_about, search_classical_texts — L0FR Stream C tools
// that existed fully-implemented in tools/read_classical_text.ts since 2026-06-07 but were
// never imported/registered here (see the import comment above). 83 + 5 = 88.
// KNOWN RESIDUAL (not fixed by this lane — flagged, not silently left inaccurate): a live
// raw `tools/list` probe against production on 2026-07-25 (SATYA_SHESHA_MCP_SURFACE_NOTE_v1_0.md)
// returned 111 tools for the 'full' profile, well above this hand-maintained tally. This
// constant has been drifting stale for multiple PRs (it is manually incremented per-change,
// not mechanically derived from the actual registration calls above) — /health's `tools`
// field should NOT be treated as the authoritative live tool count; `tools/list` is. A
// follow-up should replace this constant with a value computed from the request-scoped
// server's own registered-tool count rather than hand-maintaining it further.
const REGISTERED_TOOL_COUNT = 88

app.get('/health', (_req: Request, res: Response) => {
  res.json({
    status: 'ok',
    service: 'marsys-mcp',
    version: '1.0.0',
    tools: REGISTERED_TOOL_COUNT,
    stream_g_capabilities: ['compute_natal_positions', 'query_dasha_periods', 'query_special_lagnas'],
  })
})

// ── Start server ──────────────────────────────────────────────────────────────

const port = parseInt(process.env['MCP_PORT'] ?? '8080', 10)
app.listen(port, () => {
  console.log(`[mcp:server] MARSYS-JIS MCP server listening on :${port} (Stream G: +3 PyJHora tools)`)
  console.log(`[mcp:server] Platform URL: ${process.env['PLATFORM_URL'] ?? 'http://localhost:3000'}`)
})
