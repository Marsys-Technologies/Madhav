---
artifact: RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC
canonical_id: RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC
version: 1.0
status: DRAFT
created: 2026-06-27
author: Cowork (research synthesis) — for native Abhisek Mohanty
classification: D-GROUNDTRUTH deliverable (1 of 4) — the LLM-facing face
parent: RETRIEVAL_SYSTEM_DESIGN_APPROACH (§B.1)
sourcing: official primary-source provider documentation read directly (URLs cited inline + §Sources)
freshness_caveat: provider docs advance fast; pin model identifiers and re-verify the conflict matrix before any implementation. Captured 2026-06-27.
changelog:
  - v1.0 (2026-06-27): Initial per-provider cited best-practices spec for Anthropic / Gemini / OpenAI / DeepSeek + MCP spec (2025-11-25). Cross-provider convergence/conflict matrix + deduplicated MUST/SHOULD design-obligations checklist (MCP / chat / shared). Built from official docs read directly.
---

# RETRIEVAL GROUND-TRUTH — LLM PROVIDER BEST-PRACTICES SPEC (v1.0)

> **What this is.** The cited specification of what the official documentation of four LLM providers
> (Anthropic Claude, Google Gemini, OpenAI, DeepSeek) and the Model Context Protocol spec prescribe for
> tools, resources, prompts, schemas, caching, structured output, context, and reasoning — across both
> the external MCP channel and the internal chat/direct-API channel. It is **provider requirements our
> design must honor**, not a design of our system. It is deliverable 1 of 4 of the D-GROUNDTRUTH wave
> (see `RETRIEVAL_SYSTEM_DESIGN_APPROACH §B.1`).
>
> **Freshness.** Captured 2026-06-27 from live docs. Several figures had advanced past prior assumptions
> (OpenAI docs at gpt-5.x; DeepSeek cut over to V4, legacy `deepseek-chat`/`deepseek-reasoner` retire
> 2026-07-24; Anthropic docs canonical at platform.claude.com; MCP latest spec 2025-11-25). Re-verify
> before implementation.

---

## PART 1 — PER-PROVIDER SPECS (cited)

### 1. ANTHROPIC CLAUDE (Messages API)

**Tools.** Top-level `tools` array; each tool: `name` (`^[a-zA-Z0-9_-]{1,64}$`), a detailed plaintext
`description`, `input_schema` (JSON Schema), optional `input_examples`; composable `cache_control`,
`strict`, `defer_loading`, `allowed_callers`. Verbatim, the #1 lever: *"Provide extremely detailed
descriptions. This is by far the most important factor in tool performance"* — aim for 3–4+ sentences.
Consolidate related operations (use an `action` param), namespace (`github_list_prs`), return semantic/
stable identifiers not opaque references. Parallel tool calls default on (`disable_parallel_tool_use` to
limit). Tool results: a `user` message with `tool_result` blocks that **must immediately follow** the
corresponding `tool_use` and come **first** in the content array; treat tool content as untrusted.
`tool_choice`: `auto`/`any`/`tool`/`none` (only `auto`/`none` valid under extended thinking). Strict-mode
limits: ≤20 strict tools, ≤24 optional params, ≤16 union params, 180s grammar compile.

**Structured output (GA).** `output_config.format={type:"json_schema",schema}` and `strict:true` on tools
→ grammar-constrained, schema-guaranteed. Combine `tool_choice:{type:"any"}`+`strict:true` to guarantee a
conformant tool call. Required props ordered first. Refusal → `stop_reason:"refusal"`; truncation →
`max_tokens`. Prefilling incompatible with JSON outputs.

**Prompt caching (MUST mark).** Not automatic by default — mark up to 4 `cache_control` breakpoints; prefix
order tools→system→messages; **100% exact prefix match** required (never cache a block with a timestamp).
Minimum ~1,024 tokens (model-varying). TTL 5min default / 1h optional; write ×1.25 (5min) or ×2 (1h),
read ×0.1.

**Context.** 1M on top models (Opus 4.x, Sonnet 4.6), 200K others; *"context rot"* degrades recall as
tokens grow; overflow → `stop_reason:"model_context_window_exceeded"`.

**Extended thinking.** `thinking={type:"enabled",budget_tokens:N}`. **Critical for tools:** *"you must pass
thinking blocks back to the API for the last assistant message… complete unmodified"* — including
`redacted_thinking` (filtering on `type=="thinking"` silently breaks the protocol). Incompatible with
temperature/top_k/forced tool use.

**MCP.** MCP connector (HTTPS only, tool calls only, not ZDR, not on Bedrock/Vertex). Engineering guidance:
fewer consolidated tools; *"resolving arbitrary alphanumeric UUIDs to more semantically meaningful…
language (or even a 0-indexed ID scheme) significantly improves Claude's precision… by reducing
hallucinations"*; expose `response_format` enum (concise/detailed); paginate/filter/truncate; ~25,000-token
default response cap. Code-execution-with-MCP: present servers as code APIs + progressive disclosure to cut
tokens.

### 2. GOOGLE GEMINI

**Function calling.** `name` (no spaces/special chars), crucial `description`, `parameters` (OpenAPI-3.0.3
schema subset; `enum` for fixed sets). Return `functionResponse` with the **exact `id`** from the
`functionCall`. Parallel + compositional calling supported. Modes: `VALIDATED` (default, reduces malformed
calls), `AUTO`, `ANY` (+`allowed_function_names`), `NONE`. Soft guidance: *"10–20 active tools maximum"*;
only a subset of OpenAPI schema supported; ANY mode may reject large/deeply-nested schemas.

**Structured output.** `response_format` with a JSON-Schema subset; honors key order (2.0 needed
`propertyOrdering`). Verbatim: *"it does not guarantee the values are semantically correct. Always
validate"*; *"ignores unsupported properties"*; may reject large/deeply-nested schemas.

**Caching.** Implicit (auto on 2.5+, no saving guarantee) + explicit (`caches.create` → `cached_content`
handle, **guaranteed** saving). Implicit min 1024/4096 (Flash/Pro). Verbatim: *"Try putting large and common
contents at the beginning"*; *"Cached content is a prefix to the prompt."* Explicit TTL default 1h, no bounds;
billed by tokens + storage time.

**Context.** ~1M (2.5 Pro: 1,048,576 in / 65,536 out). Verbatim: *"put your query/question at the end of the
prompt."* Single-needle ~99%, multi-needle degrades.

**Thinking.** Gemini 3: `thinkingLevel` (can't fully disable; can't disable on 3.1 Pro). 2.5: `thinkingBudget`.
**Thought signatures** (encrypted) *"required for function calling"* — *"Always send the `thought_signature`
back inside its original Part"*; never merge/concat parts with signatures. Pricing = output + thinking tokens.

**MCP.** Remote MCP (Interactions API): `{type:"mcp_server",name,url,headers,allowed_tools}`. **Streamable
HTTP only (no SSE); not on Gemini 3 yet; no `-` in server names (use snake_case).**

### 3. OPENAI (Responses API + Chat Completions)

**Function calling.** Shape differs by API: Chat Completions nests under `function:{…}`; Responses is flat.
Verbatim: *"We recommend always enabling strict mode"* → `additionalProperties:false` + **all fields in
`required`** (optionals = null union). *"Keep the number of initially available functions small."* Soft cap
*"fewer than 20 functions."* Parallel on by default (`parallel_tool_calls:false` to disable; not with
built-in tools). Outputs: Responses `function_call_output{call_id}` / Chat `role:"tool"{tool_call_id}`;
output should be a string; pass reasoning items back with tool outputs. `tool_choice`:
auto/required/none/named + **`allowed_tools`** (preferred — preserves prompt-cache savings).

**Structured outputs.** Verbatim guarantee: *"ensures the model will always generate responses that adhere
to your supplied JSON Schema."* Prefer over `json_object` (which guarantees valid JSON, not schema). Limits
raised to 5,000 props / 120,000 chars / 1,000 enums; value constraints (`pattern`/`minLength`/…) unsupported.
Programmatic `refusal` field.

**Prompt caching (automatic).** Verbatim: *"works automatically… no code changes… no additional fees…
gpt-4o and newer."* Min 1,024 tokens; routes on a prefix hash (~first 256 tokens). **Exact prefix match**
incl. images and tools. *"place static content… at the beginning… variable content… at the end."* TTL
5–10min (up to 1h off-peak; 24h via `prompt_cache_retention`). No write cost; up to 90% input reduction.
`prompt_cache_key` for routing; `cached_tokens` telemetry.

**Context.** gpt-5.4 1M / 128K out; 272K standard threshold (extended-context billing above); 4o 128K;
o-series ~200K.

**Reasoning.** `reasoning.effort` none→xhigh. Reasoning tokens invisible, billed as output. Preserve via
`previous_response_id` or `reasoning.encrypted_content` (stateless/ZDR). Verbatim for tools: *"pass back any
reasoning items returned with the last function call."* Reserve ≥25,000 tokens for reasoning+output; don't
over-prescribe CoT.

**MCP.** `mcp` built-in tool: `{type:"mcp",server_label,server_url,require_approval}`; Streamable HTTP or
SSE. OAuth `authorization` re-sent every request. `allowed_tools`; `require_approval` defaults to requiring
approval. Servers are untrusted third parties; private servers need a Secure MCP Tunnel; `defer_loading`
for large servers; OpenAI-maintained Connectors via `connector_id`.

### 4. DEEPSEEK (V4; legacy retires 2026-07-24)

**Build against `deepseek-v4-flash`/`deepseek-v4-pro`.** OpenAI-compatible base + Anthropic-compatible
endpoint. **Function calling** OpenAI-compatible, now first-class; `disable_parallel_tool_use` accepted but
ignored. **Thinking-mode trap:** for turns that perform tool calls, `reasoning_content` **must be passed
back** (400 otherwise). Beta `strict` mode (`/beta`): all object props required + `additionalProperties:false`;
no length/items constraints.

**Structured output.** `response_format:{type:"json_object"}` only — **no content-level strict schema.**
Verbatim: *"Include the word 'json'… and provide an example"*; set `max_tokens` to avoid truncation; may
*"occasionally return empty content."* → application-side validate + retry is mandatory.

**Caching (automatic, on disk, free).** Exact-prefix from token 0; partial/middle matches don't hit; **min
unit 64 tokens.** Put stable prefix first. `prompt_cache_hit_tokens`/`miss_tokens` telemetry.

**Context.** V4: 1M / 384K out (was 64K under V3/R1).

**Reasoning.** Legacy R1: `reasoning_content` must NOT be fed back (400); reasoner had no function calling.
**V4 thinking INVERTS this:** with a tool call between user messages, `reasoning_content` must be passed
back; tools AND JSON supported in thinking mode. → version-pin this behavior.

**MCP: none.** DeepSeek does not implement MCP; via its Anthropic-compatible endpoint `mcp_servers` is
ignored and MCP content blocks unsupported. Our MCP server must work as a **plain tool-calling backend** for
DeepSeek.

### 5. MCP SPECIFICATION (2025-11-25)

**Tools (model-controlled).** Declare `tools` capability; `tools/list` (paginated) + `tools/call`. Tool:
`name` (1–128 chars, `[A-Za-z0-9_.-]`, no spaces), optional `title`, `description`, `inputSchema` (valid
JSON Schema object, **not null**, default dialect 2020-12), optional `outputSchema`/`annotations`/
`execution.taskSupport`. Result content: text/image/audio/resource_link/embedded resource; `isError`.
**Two error mechanisms:** protocol errors (JSON-RPC) vs tool-execution errors (`isError:true`, incl. input
validation — clients SHOULD feed these to the model for self-correction).

**Structured content.** Return `structuredContent` (JSON) AND, for back-compat, the serialized JSON in a
`text` block. If `outputSchema` given: server MUST conform, client SHOULD validate.

**Resources (application-driven).** `resources/list`+`resources/read`+`resources/templates/list`+subscriptions.
Templates use RFC 6570 `uriTemplate`. Contents text or base64 `blob`. Annotations: `audience`, `priority`,
`lastModified`.

**Prompts (user-controlled).** Slash-command style; `prompts/list`+`prompts/get(arguments)`.

**Pagination.** Opaque cursor (`nextCursor`/`cursor`); server owns page size; clients MUST treat cursors as
opaque. On all list ops.

**Security.** Annotations (`readOnlyHint`/`destructiveHint`/`idempotentHint`/`openWorldHint`) are untrusted
hints. Human-in-the-loop SHOULD be able to deny invocations; validate inputs, access-control, rate-limit,
sanitize outputs.

---

## PART 2 — CROSS-PROVIDER CONVERGENCE & CONFLICT

### Convergence (the safe intersection to design to)

- **Schema language:** all accept a JSON-Schema core — `type`/`properties`/`required`/`enum`/`items`/
  `description` + nested objects/arrays — accepted by all four.
- **Strict-object rule:** where constrained decoding exists, all converge on `additionalProperties:false` +
  all-props-required (optionals as null union).
- **Value constraints dropped/ignored everywhere** (`minLength`/`maximum`/`pattern`/`format`) → restate in
  `description`, validate in code.
- **Description is the #1 selection lever** for all four; keep active tool sets small (<~20).
- **tool_choice 4-way model** (auto / force-any / force-named / none) exists across all.
- **Caching = leading static prefix + exact-prefix match** everywhere → design `[stable prefix]→[variable tail]`.
- **Structured output is syntactic not semantic** everywhere → always re-validate values.
- **Query at the END** of long prompts; long context degrades.
- **Reasoning artifacts round-tripped unmodified when a tool was used** across all four.

### Conflict (per-profile handling or native decision required)

| Axis | Anthropic | Gemini | OpenAI | DeepSeek |
|---|---|---|---|---|
| Tool-arg type | parsed object | parsed object | **JSON string** | **JSON string** |
| Tool-result wire format | tool_result block, results-first user msg | functionResponse+id | function_call_output / role:tool | role:tool |
| Caching control | **must mark** ≤4 breakpoints, write cost | implicit + explicit handle | automatic, free | automatic, free, 64-tok unit |
| Structured-output strictness | grammar guarantee | schema, values may err | strict guarantee | **json_object only, no schema** |
| MCP | client/connector (HTTPS, tools only) | Remote (Streamable-HTTP only, not G3, no `-`) | mcp tool + connectors (approvals) | **none** |
| Reasoning artifact | thinking/redacted blocks | thought_signatures per Part | reasoning items/encrypted | reasoning_content (version-conditional) |
| Context floor (cross-path) | 200K non-top | ~1M | 272K threshold | 64K legacy / 1M V4 |
| Parallel disable | yes | (none) | yes | accepted-but-ignored |

---

## PART 3 — DESIGN OBLIGATIONS CHECKLIST (actionable)

### MCP-channel (our server)
- Tool names 1–128 chars `[A-Za-z0-9_.-]`, **avoid `-`** (Gemini), prefer snake_case/dot; unique.
- `inputSchema` always a valid JSON Schema object (never null), dialect 2020-12.
- Detailed intent-rich descriptions + human `title`.
- Provide `outputSchema` for structured tools; return `structuredContent` + serialized JSON `text` block.
- Set `annotations` honestly; return input-validation failures as tool-execution errors (`isError:true`).
- High-signal token-bounded responses: pagination + filtering + truncation + `response_format`/verbosity enum + default cap.
- Resolve opaque UUIDs → human-meaningful names / 0-indexed IDs; drop low-level identifiers.
- Consolidated workflow tools over granular; namespace; keep active set small.
- Use resources for app-driven context, prompts for user-driven; RFC-6570 templates; annotations.
- Cursor pagination on every list; server owns page size; invalid cursor → -32602.
- Serve over HTTPS Streamable HTTP (the cross-provider intersection); validate/access-control/rate-limit/sanitize.
- Function as a plain backend for DeepSeek; don't assume Gemini-3 reach; tolerate OpenAI approval flow + `defer_loading`; offer progressive-disclosure discovery for large catalogs.

### Chat / direct-API
- One internal tool model → per-provider serializers (shape, arg-type, result format, caching, reasoning).
- Enable strict/constrained modes where available; `additionalProperties:false`+all-required+null-unions; don't rely on value constraints.
- Parse `arguments` as JSON string for OpenAI & DeepSeek; consume object for Anthropic & Gemini.
- Emit provider-exact tool-result wire format + ordering.
- Aggregate N parallel tool calls regardless of profile.
- Prefer native structured output; for DeepSeek fall back to `json_object` + "json" word + example + max_tokens + **validate+retry**.
- Always re-validate output values; handle refusal/truncation.
- `[stable prefix]→[variable tail]`; Anthropic explicit breakpoints (≤4, never timestamped); Gemini explicit cache for big reused context; set routing keys; read cache telemetry; keep prefix >4,096 tokens.
- Round-trip reasoning artifacts per profile + per DeepSeek version; budget for invisible reasoning tokens (reserve ≥25,000); set effort per task class.
- Budget cross-model paths to the **smallest** window; query at END; curate not dump.

### Shared (both channels)
- Single internal tool/schema model + per-provider adapters (the four conflict on every adapter axis).
- Author to the safe intersection; constraints in descriptions + code.
- Treat all model-facing tool/resource content as untrusted (injection).
- Validate every structured output regardless of provider guarantee.
- Descriptions "like onboarding a new hire"; small active tool counts; semantic IDs over UUIDs.
- Instrument cache-hit + reasoning-token telemetry.
- Pin model identifiers; track deprecations (DeepSeek legacy 2026-07-24); version per-profile reasoning round-trip rules.

---

## Sources

Anthropic: platform.claude.com/docs (define-tools, handle-tool-calls, tool-reference, parallel-tool-use,
strict-tool-use, structured-outputs, prompt-caching, context-windows, extended-thinking, mcp-connector);
anthropic.com/engineering (writing-tools-for-agents, code-execution-with-mcp, effective-context-engineering).
Gemini: ai.google.dev/gemini-api/docs (function-calling, generate-content/function-calling, structured-output,
caching, long-context, models/gemini-2.5-pro, thinking).
OpenAI: platform.openai.com/docs/guides (function-calling, structured-outputs, prompt-caching, reasoning,
tools-remote-mcp); docs/models.
DeepSeek: api-docs.deepseek.com (quick_start/pricing, news/news260424, guides/tool_calls, guides/json_mode,
guides/kv_cache, guides/reasoning_model, guides/thinking_mode, guides/anthropic_api).
MCP: modelcontextprotocol.io/specification/2025-11-25 (server/tools, server/resources, server/prompts,
utilities/pagination, basic, changelog, schema); blog.modelcontextprotocol.io tool-annotations.

*End of RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC v1.0 — D-GROUNDTRUTH deliverable 1 of 4.*
