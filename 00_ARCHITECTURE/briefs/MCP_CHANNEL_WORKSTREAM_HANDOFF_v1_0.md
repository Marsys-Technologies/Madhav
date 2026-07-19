---
artifact: MCP_CHANNEL_WORKSTREAM_HANDOFF_v1_0.md
canonical_id: MCP_CHANNEL_WORKSTREAM_HANDOFF
version: 1.0
status: CURRENT — ACTIVE HANDOFF
authored_by: Claude (Cowork) 2026-07-19
purpose: >
  Self-contained handoff for a dedicated MCP-channel design conversation.
  Carries everything a fresh session needs: project context, verified current
  state of the MCP surface, settled decisions that constrain the work, the
  scope boundary against the Paripraśna workstream, the open forks this
  workstream must resolve, and the findings that must not be relitigated.
parent_document: 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md
read_first: CLAUDE.md (project root)
---

# MCP Channel — Workstream Handoff

> **How to use this document.** Paste or reference this at the top of a new
> conversation. It is written to be sufficient on its own; the reader should
> not need the originating conversation. Read `CLAUDE.md` at the project root
> first for governance, then this. The parent architecture document
> (`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`) is the system-wide context —
> read §1, §2, §4, §6, §8 of it; the rest is Paripraśna-specific and out of
> scope here.

---

## §1 — What this workstream is

Design the **MCP channel** of MARSYS-JIS end to end: what a user connecting
the MCP from an external LLM client receives, how the surface is shaped, how
profiles and entitlements are resolved, what the composite consultation tool
(`prashna_ask`) is, and how the tool registry is projected onto that surface.

This is one of two conversation channels the instrument exposes. The other —
**Paripraśna**, the in-portal chat surface — is being designed in a parallel
conversation and is **out of scope here** (§4).

### §1.1 The one-sentence framing

The MCP channel exposes the instrument to an LLM the project does not control,
which means every quality guarantee the engine provides must either be carried
by a composite tool that runs our own loop, or be encoded into the envelope
itself — because prose written by a foreign model never crosses our boundary
and therefore cannot be gated.

---

## §2 — Project context (minimum sufficient)

**MARSYS-JIS** is an LLM-operated Vedic Jyotish instrument. It reads a birth
chart with acharya-grade depth, surfaces patterns across layers no individual
astrologer could hold in working memory, and makes time-indexed, probabilistic,
calibrated predictions testable against lived reality.

**The build arc is complete.** Six layers, all sealed or closed:

| Layer | Name | Contents |
|---|---|---|
| L0 | Brahmagyan | Global reference tables |
| L1 | Gaṇita | `chart_facts`, `chart_dashas`, `chart_divisionals` — 9 assets + service |
| L2 | Bodha | `bodha_*` — 14 assets |
| L3 | Kāla | `kala_*` — 12 assets |
| L4 | Phala | `phala_*` — 9 assets |
| L5 | Mīmāṃsā | `mimamsa_*` — 12 assets. **Sealed in STRUCTURAL mode** — empirical calibration values are empty by design and fill only as prediction→outcome data accrues. |

Asset-id prefixes `bg_* ga_* bo_* ka_* ph_* mi_*`. **Never show "L0–L5"
externally** — the Sanskrit names are the external lexicon.

**Canonical chart** (the native's own): `482012f1-710e-4a25-994a-93821f5871aa`.

**Non-negotiable principles that bind this workstream:**

- **B.1** — facts/interpretation separation by layer.
- **B.3** — derivation-ledger mandate: every L2+ claim carries the L1 `fact_id`s
  it consumes.
- **B.10** — no fabricated computation. `total: null` in a coverage stamp is
  the honest value; never invent one.
- **B.11** — Whole-Chart-Read discipline: every query routes through L2 Bodha
  synthesis first, then produces its domain answer.
- **§N.6 Serving Density Principle** — (1) never present catalog/label matches
  as confirmed findings; (2) the densest layer is protected first by a budget
  trim (`hardFloor`); (3) the verdict layer is never empty when grounding data
  exists — an honest empty is reported via `judgment_flags`, never substituted
  with a hollow-but-populated envelope; (4) density signalling is data, not
  narration.

---

## §3 — Verified current state of the MCP channel

All facts below were verified against source during the 2026-07-19
investigation. Treat as ground truth; re-verify only if a decision hinges on
an exact count.

### §3.1 Topology today

`platform-mcp/` is a **separate Node/TS project** (own tsconfig, NodeNext, no
`@/` path mapping) running an MCP `StreamableHTTPServerTransport` over Express
at `POST /mcp`, stateless per request.

**It has no database access.** Every real call proxies back to the `platform`
Next.js app over HTTP via `POST /api/retrieval/capability` (`{uri, args}` →
handler), gated by `MCP_INTERNAL_TOKEN` plus a per-call `authorizeChartAccess`
entitlement check. This isolation is a deliberate security property.

Two other cross-process seams: `/api/mcp/surface-spec` (per-model-family
surface constraints) and `/api/mcp/session` (session + pin state).

### §3.2 The tool surface

**~118 tools**, registered **imperatively** — `platform-mcp/src/server.ts`
(~28KB) imports ~20 `register*Tools(server, principal)` functions and calls
each inside a per-request server factory. There is no single tool table; the
authoritative census is a **hand-maintained comment block at
`server.ts:459–517`**.

By prefix:

| Prefix | Count | Layer |
|---|---|---|
| `ref_` | 25 | L0 reference/corpus — largest family |
| `ganita_` | 22 | L1 computed facts |
| `bodha_` | 9 | L2 signals/graph/digest |
| `kala_` | 7 | L3 temporal |
| `phala_` | 6 | L4 outlook/anchors |
| `mimamsa_` | 4 | L5 calibration/LEL/outcome |
| `synth_` | 2 | chart brief, tail divergence |
| `util_` | 1 | intent classify |

Plus **~40 unprefixed legacy canonical names** still live (`get_positions`,
`assess_career`, `query_chart_facts`, `judgment_query`, `pact_query`,
`select_chart`, `recall_session`, `plan_retrieval`, …).

**45 of the 118 are pure naming aliases** (`tools/register_p1_aliases.ts`,
BA-P1, 2026-07-03) projecting legacy names onto the `layer_noun_verb`
convention. **6 aliases remain DEFERRED** (`recall_session`→`session_recall`,
`list_my_charts`→`catalog_charts_list`,
`holistic_bundle_chart_facts`→`bodha_bundle_get`, and three others).

Registration paths, by maturity:

1. **Registry-backed** (`tools/registry_bridge.ts`) — 20 tools (12 D7 workflow
   + 8 D8 apex) resolving to `marsys://` URIs. **This is the intended path.**
2. **Sidecar paths** — `mimamsa_outcome`, `phala_event_anchors`, marked in
   `server.ts` comments as *"KEYSTONE REQUEST: … has no registry primitive.
   Still served via sidecar until the registry primitive lands."*
3. **Alias layer** — the 45 above.

### §3.3 The shared registry

Since the **D7 Chat-Channel Migration (2026-06-28)**, chat and MCP already
share **one** registry source: `platform/src/lib/retrieval/registry/`. The old
`lib/retrieve` + `tool_catalogue` were retired. Git tag:
`retrieval-d7-chat-migration-complete`. A hard guard survives in
`api/chat/consult/route.ts:76–77`:

```
// D7 Step 4: getTool() replaced with registry-backed getToolByName(); tool_catalogue RETIRED
// DO NOT restore lib/retrieve imports — see RETRIEVAL_D7_CALLER_MAP_v1_0.md §2.1
```

`registry/types.ts` (428 lines) defines `CapabilityDescriptor` as a
**discriminated union on `scope: 'per_chart' | 'global'`**, where `per_chart`
*type-level requires* `chart_id` in `required_inputs`. Build-time enforcement
by `chart_agnostic_gate.ts` (356 lines + 573 lines of tests): **no default
chart UUID is injectable anywhere in the pipeline.**

The descriptor carries a **frozen D1 topology contract**
(`amendment_version: 1`, `D1_AMENDMENTS` empty — additions require a versioned
amendment): `archetype` (8 retrieval archetypes), `traversal_level`
(L-ORIENT → L-SYNTH), `tool_role` (umbrella/drill/leaf/graph/…),
`drill_children`, `emits_references` (F1 reference-don't-repeat), `grounds_to`
(F3 layer-resolution-DOWN), `lel_capable`.

`density_contract` (`types.ts:207`) — `{max_verdict_bytes, max_digest_bytes,
paginated, facets[], empty_reason}` — is **optional and declared by only 6 of
~118 capabilities**: `get_dasha_lord_capability`, `get_vichara`,
`get_yoga_dosha`, `get_yoga_firings`, `register_d9_judgment` (judgment_query),
`L2/query_signals`.

`tool_name_bridge.ts` (545 lines) is the authoritative legacy-name →
`marsys://` URI map and also owns the MCP surgical whitelist.

> **⚠ CORRECTION 2026-07-19 — read before §3.4.** This brief's §3.4 claimed the
> envelope mirror at `platform-mcp/src/lib/envelope.ts` is hand-maintained and
> "the codegen lane never landed." **Both claims are false.** That file does not
> exist; the envelope is generated at `platform-mcp/src/generated/envelope.ts`
> by `scripts/generate_envelope.ts`, with four codegen scripts in
> `package.json` (`codegen:envelope`, `codegen:registry-shims`, `codegen`,
> `codegen:check`). `scripts/generate_registry_shims.ts` also exists — **3 pilot
> instruments, deliberately NOT wired in**, per the strangler discipline the
> generator itself cites (brief §6.2: *"migrate one instrument at a time, behind
> a parity gate; no single PR regenerates the estate"*), which implements the
> binding mandate at `RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md:538` §19.
>
> **Three consequences for this workstream:** (1) the monorepo is **not**
> load-bearing — codegen already shares contracts across the process boundary;
> (2) the path to generated projections is to **extend the existing shim
> generator**, incrementally, not to convert the workspace; (3) **the alias
> cutover must be a strangler migration, not "one release, one breaking
> change"** — §6/OT-10 and §8 item 6 are revised accordingly.
>
> **A real gap this surfaces:** §19's mandate says "codegen step in CI."
> `codegen:check` exists and **no workflow invokes it** — eight workflows, none
> referencing codegen. **Contract drift is currently undetected.** Wiring it is
> a one-line, high-value first action.
>
> **Corrected counts:** aliases are **55**, not 45 (55 actual / 47 in the file
> header / 45 in the `server.ts` census — all three disagree). Tools:
> `REGISTERED_TOOL_COUNT = 120`, raw `server.tool(` count **126**. The
> hand-maintained census is wrong in both directions — which is precisely what
> generated projections exist to eliminate.

### §3.4 The v3 envelope

`platform/src/lib/retrieval/envelope.ts` (453 lines), with a
**hand-maintained byte-structural mirror at `platform-mcp/src/lib/envelope.ts`**.
The process boundary prevents importing; **every edit must be made twice.** The
codegen lane that was to supersede this never landed.

```
resolveEnvelopeFormat(requested) → requested === 'v3' ? 'v3' : 'legacy'   // default legacy
V3Envelope extends LegacyEnvelope {
  response_format: 'v3', chart_header, epistemic, timing, coverage, verdict,
  ranking_basis, grounding, drill_pointers, judgment_flags, pagination, trim_report
}
```

v3 is **strictly additive, strictly opt-in**; the default flips only after the
W4 answer-rubric battery passes. Supporting machinery: `EpistemicGrade` is a
closed 7-value vocabulary derived live from `verification_pass_status` ratios;
`buildCoverageStamp(family, served, total)` where `total: null` is honest;
`buildHonestPagination`; cursor encode/decode.

`judgment_flags` is the honest-gap channel. Known emitters: `session_pin.ts`
(`chart_rebuilt_mid_session_pin_refreshed`), `register_d9_judgment.ts`
(`bearing_yogas_empty`, `timing_anchored_false`), `get_yoga_dosha.ts`
(`catalog_only_rows_present`).

### §3.5 Response budget

`platform-mcp/src/lib/response_budget.ts` (514 lines) — **structure-aware, not
byte-truncating**. Callers declare `TrimmableSection`s
(getArray/setArray/minKeep/recover pointer); it shrinks the heaviest section
first, halving to floors, re-measuring. Every cut emits a `TrimReportEntry`
with a `recover_via` pointer.

Two things any consumer must know:

- **PASS 2 is a hard-cap fallback that floors every section to 0**, overridden
  only by the D-1.5a-added `hardFloor: true` opt-in.
- `BudgetResult` exposes a flag for "still over budget after flooring
  everything" which **must not be silently swallowed**.

Distinct from `lib/retrieval/adapters/shared/result_clipper.ts`, which is
LLM-context text trimming. Do not confuse them.

### §3.6 Auth and sessions

**Full OAuth 2.0** in `platform-mcp/src/oauth/` — authorize, callback, token,
discovery, OpenID configuration, token_store, dynamic client registration —
backed by `api/mcp/oauth/*`. Plus an API-key path
(`validateMcpKeyFromHeader`, `api/mcp/keys`). Authorization is per-chart via
`authorizeChartAccess` / `remoteAuthorize`, with an admin chart-grants UI at
`api/admin/users/[id]/chart-grants`.

**Sessions:** `mcp_sessions` keyed on `user_uid` + opaque `session_key`
(default `'default'`), with a `state_json` blob. Served via `api/mcp/session`
and `api/mcp/sessions`; helper at `platform-mcp/src/lib/session.ts`.
`recall_session` re-checks entitlement on the stored `active_chart_id` before
returning it — a revoked grant means the chart is silently omitted plus an
advisory, never replayed.

**Session pin** (`platform/src/lib/retrieval/session_pin.ts`) pins
`{priors_version, formula_versions, ranking_config, build_id,
now_context_date}` per **explicit** chart_id (never inferred — the §31.3
collision mitigation), re-keyed by chart_id inside `state_json` so two chart
contexts under one session get independent pins. `detectBuildDrift()` emits
`judgment_flags: ['chart_rebuilt_mid_session_pin_refreshed']` and always
returns the freshly-refreshed pin, never a stale one.

### §3.7 Planning surfaces exposed over MCP

- **`plan_retrieval`** (`platform-mcp/src/tools/register_vidhi_plan.ts`, 120
  lines, D-2 Lane V-2) backed by `platform/src/lib/vidhi/`. Given a question
  and/or partial DR-8 scope tuple it returns: the echoed resolved
  `scope_tuple` (for correction before execution), the compiled **acharya
  floor + machine band** (each item naming its live tool + args), a
  **completeness receipt** (served/empty/dark per floor item, where every
  `dark` item cites the OPEN CR that makes it a known gap), and
  `capability_version`. It implements a **staleness kill**: a caller passing a
  stale `client_capability_version` gets `capability_stale: true` plus a
  `notifications/tools/list_changed` emission. It is the *fallback* path; the
  primary is the `vidhi_plan` MCP prompt.

- **`intent_scope_classifier.ts`** — the DR-8 scope-tuple producer
  `{intent, domains, width, depth, horizon, intervention, entitlement}`.

### §3.8 Other current-state facts

- **`reading_notes.ts`** (D-2 Lane V-3) serves verified per-chart reading notes
  so a reading agent inherits verified structure. **Currently hardcoded to one
  chart** (`CANONICAL_CHART_ID`, content as a TS string constant). Shipped as a
  *tool* rather than the briefed *resource* form for scope-warden reasons.
- **`mimamsa_outcome_record`** → python-sidecar → Brier score
  `(confidence − outcome_binary)²` → `mimamsa_calibration` (chart_id,
  technique, ayanamsha_id, brier_score, sample_size, `source_citation NOT NULL`).
- **`api/mcp/surface-spec`** → `getMcpSurfaceSpec(family)` provides per-family
  max_tools / name pattern / dual-output / transport, explicitly designed so
  *"both channels derive surface constraints from the SAME call."*

---

## §4 — Scope boundary

### §4.1 The architectural rule this boundary follows

**The engine is door-agnostic and lives outside both channels.** Paripraśna is
a browser-side wrapper; the MCP edge is a protocol-side wrapper; both call the
same engine.

```
 ┌─ PARIPRAŚNA (out of scope here) ───────────────────────┐
 │  composer · conversation service · thread history ·    │
 │  summaries + RAG recall · stream protocol · render ·   │
 │  disclosure-tier projection · Samīkṣā UI · persistence │
 └───────────────────────┬────────────────────────────────┘
                         │  ask(chart_id, question)   ← D-15, D-16
                         ▼
 ╔═══ THE ENGINE (shared — constrains this workstream, ═══╗
 ║      but is not owned by it)                           ║
 ║  planner pipeline → PlanReceipt                        ║
 ║  agentic loop · ModelPlane                             ║
 ║  registry + capability dispatch                        ║
 ║  v3 envelope + response budget                         ║
 ║  grounding gate · register lint · sentinel rewrite     ║
 ║  prediction detection                                  ║
 ╚═══════════════════════▲════════════════════════════════╝
                         │  same call
 ┌───────────────────────┴────────────────────────────────┐
 │─ MCP EDGE (THIS WORKSTREAM) ───────────────────────────│
 │  OAuth · profile + projection selection · prashna_ask  │
 │  raw tool dispatch · MCP serialization · session       │
 │  semantics · entitlement + cost caps                   │
 └────────────────────────────────────────────────────────┘
```

**The design test:** the engine must never branch on which door it is serving.
If any code inside the engine asks "am I in chat or MCP?", the boundary is
wrong. The engine must be callable **headlessly** — no browser, no
conversation row, no stream.

### §4.2 In scope for this workstream

- MCP surface shape: which projections exist, how they are generated from the
  registry, how a client is assigned one.
- Profile selection and entitlement (see OT-10, §6).
- `prashna_ask` — its contract, transport semantics, cost governance, and
  entitlement gating.
- Raw tool dispatch and the `marsys_drill` dispatcher pattern.
- Alias removal execution and the canonical naming cutover.
- MCP session semantics under D-05 (no conversation transcript).
- OAuth issuer decision and identity spine (OT-5).
- The MCP edge's relationship to `@marsys/contract` and the envelope mirror
  deletion.
- Envelope self-sufficiency: what a foreign LLM must be able to read correctly
  without any gate of ours running (§7.2 — this is the workstream's hardest
  problem).

### §4.3 Out of scope — do not design these here

- Paripraśna's UI, streaming render protocol, three-region layout, scroll and
  caret discipline, progressive markdown.
- The conversation store, canonical message parts, durable summaries, RAG
  recall.
- **Audience tiers and depth parameters — these do not exist.** See D-15 in
  §5. Do not reintroduce them under any name.
- The Samīkṣā review surface and the prediction-confirmation UX.
- The FROZEN orchestrator, `WriterBase`, and the L0–L5 build DAG. Sacrosanct.
- Chart computation.

### §4.4 Shared constructs — coordinate, do not fork

These are being designed in the parallel workstream or already exist. This
workstream **consumes** them and may raise requirements against them, but must
not redesign them unilaterally:

| Construct | Owner | Note |
|---|---|---|
| The unified planner pipeline → `PlanReceipt` | Engine | `plan_retrieval` exposes it over MCP |
| The agentic loop service | Engine | `prashna_ask` invokes it |
| `CapabilityDescriptor` + `density_contract` + the `register` block | Registry | This workstream drives the projection logic |
| v3 envelope | `@marsys/contract` | Mirror deletion is in scope here |
| ModelPlane tiers A/B/C | Engine | `quirks.max_tools` drives projection selection |
| Session pin | Shared | Promoted to all conversations |
| Prediction ledger | Shared, channel-agnostic **by necessity** | See §7.3 |

---

## §5 — Settled decisions that constrain this workstream

From `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §1`. Binding unless explicitly
revisited with the native.

| # | Decision |
|---|---|
| **D-03** | The channels are **not** separately named. Paripraśna is the *capability*; portal and MCP are transports. |
| **D-04** | Exactly two channels. No third is designed for. |
| **D-05** | **Cross-channel conversation transcript portability is DROPPED.** History lives in Paripraśna only. Rationale: the MCP protocol makes client-side assistant text structurally unrecoverable, so "identical transcripts" was a promise the architecture could not keep. |
| **D-08** | **One registry**, sole source of truth; every serving surface is a **generated projection** of it. Reconciled form: *one registry, many generated projections* (native assent pending — OT-7). |
| **D-09** | Guest = a user analyzing charts on the portal. The native is a guest with super-admin role. Plain guests exist. Multi-user, role-differentiated, chart-entitlement-scoped. |
| **D-12** | Design for effectiveness **irrespective of effort and cost**. Existing components kept only if they fit. |
| **D-14** | Internal register (layer names, asset ids, `MSR`, `SIG.*`, table names) must not appear in user-facing prose — **universally, for every user including the native**. **See §7.2 — this is only partially deliverable on this channel.** |
| **D-16** | **The session pin is a per-turn provenance stamp, not a session pin.** §N.3 mandates delete-then-insert, so exactly one build exists in Postgres and there is no archive — **a pin cannot pin**, because the earlier build is gone. It is a witness, not a lock. Restructured: renamed **provenance stamp**; moved from mutable `mcp_sessions.state_json` to immutable per-turn message metadata; drift detected by comparing consecutive turns' stamps rather than via shared session state; **copied immutably into every prediction-ledger row** (a ledger row must never point at mutable state, or attribution corrupts silently); removed from the engine's input signature — provenance comes **out** with the answer. **Consequences for this workstream:** `mcp_sessions` loses the pin entirely, which simplifies the session model considerably under D-05; re-examine what, if anything, `mcp_sessions` still needs to hold beyond `active_chart_id`. |
| **D-15** | **No audience tier. No depth parameter. Acharya-grade by default, always.** The legacy model had a tier structure; it was deliberately torn down and must not return. Extends §N.4 ("no audience tier — writers emit all rows; serve-time governs access") from the build layer to the serve layer. **Rationale:** the tier idea smuggled in a false assumption — that plain language means a lesser reading. The opposite is true; a real acharya explains precisely in words the person can hold. **Consequences for this workstream:** `prashna_ask` takes **no `depth` and no `tier`** — its signature is `prashna_ask(chart_id, question)`. Audit detail is an affordance gated by entitlement to the underlying data, never a mode. Any surface shaping must be about *client and model capability limits* (§7.5), never about audience quality. |

**Accepted design conclusions relevant here:**

- **A-01** — pnpm monorepo with `@marsys/contract`; two deployables; the
  hand-mirrored envelope is deleted.
- **A-02** — all 45 aliases deleted; canonical naming is `layer_noun_verb`;
  `tool_name_bridge.ts` survives only for replaying persisted conversations.
- **A-03** — three projections: MCP-full, MCP-compact (~25–35 umbrellas +
  `marsys_drill`), Chat (planner-filtered per turn). **A fourth,
  MCP-consult, is proposed under OT-10.**
- **A-04** — `mutation: true` capability class; sidecar tools pulled into the
  registry.
- **A-05** — `density_contract` mandatory on every descriptor.
- **A-07** — **one agentic loop, two doors.** `prashna_ask` is the second
  door.
- **A-10** — session pin promoted from MCP-only to all conversations.
- **A-19** — NO-LEAKAGE enforced four ways: DB role grants, registry
  `calibration_context_only` flag, out-of-process ledger writer, CI canary.

---

## §6 — Open forks this workstream must resolve

| # | Fork | Options | Lean |
|---|---|---|---|
| **OT-2** | **`prashna_ask` transport semantics.** | (a) Non-streaming request/response — simple, but deep questions run minutes and clients time out. (b) MCP progress notifications — better UX, uneven client support. (c) Job handle: `prashna_ask` returns a ticket, `prashna_result` fetches. | (b) with (c) as fallback. Decides whether a job table exists. |
| **OT-5** | **MCP OAuth issuer.** | (a) Self-issued OAuth 2.1 in the edge — full control of token lifecycle; current direction. (b) Delegate to Firebase, edge as resource server — one identity spine, entitlements resolve from one user table with no mapping layer. | (b) is architecturally cleaner if Firebase can act as an OIDC provider for MCP clients. Decides whether an MCP identity *is* a portal user or merely maps to one. |
| **OT-7** | **Assent to "one registry, many generated projections."** | The native's D-08 sentence admits two readings: "same surface everywhere" vs "best surface per channel/tier". | Every downstream registry decision depends on which he meant. Needs an explicit ruling. |
| **OT-10** | **MCP profile selection — NEW, the workstream's headline fork.** | See §6.1. | (b)+(c) below. |
| **OT-6** | **Does the MCP channel get *any* durable memory?** | (a) None — raw tools + `prashna_ask`, stateless beyond the session pin. (b) Journaling tools so questions and retrievals persist even though assistant text cannot. | D-05 is safe **only if** `prashna_ask` ships. If A-07 were rejected, D-05 should be revisited. |

### §6.1 OT-10 in full — the headline fork

**The problem.** There is one MCP connection exposing a tool set.
`prashna_ask` is one tool *within* that set, alongside the raw retrieval tools.
When a user types a question into Claude Code or Cowork, **the client's model
decides which tool to call.** There is no routing logic of ours.

It may call `prashna_ask` and receive a full acharya-grade reading. Or it may
call `ganita_dashas_get` + `kala_windows_get` directly and synthesize its own
answer — bypassing our planner, our acharya floor (and therefore B.11), our
grounding gate, and our register lint.

**Same question, same connection, two radically different quality floors,
decided by a model we do not control.** This was never explicitly designed; it
fell out of "keep raw tools too."

**The distinction that matters.** Raw tools are a **practitioner/expert
surface** — drill-down investigation, debugging, research composition, and
deliberate bypass of the floor by someone who knows what they are asking for.
`prashna_ask` is the **consultation surface** — someone wants a reading and
should receive the instrument, not the database. Different people, different
competence, different intent. Leaving the choice to a foreign LLM's
tool-selection heuristics collapses the distinction at exactly the wrong
moment.

**Options:**

| | Approach | Assessment |
|---|---|---|
| **(a)** | Both tools exposed; steer via tool descriptions. | Cheap and unreliable — prompt-engineering a model we do not control, drifting by client and version. |
| **(b)** | **Two connection profiles, selected at connect time.** The MCP URL or OAuth scope determines the projection: `…/mcp` → consultation profile (`prashna_ask` + a small orienting set: `select_chart`, `list_my_charts`, chart summary — ~5 tools). `…/mcp/expert` → practitioner profile (full or compact registry projection). | Chosen deliberately by a human at connect time — exactly when "am I consulting or investigating?" has a stable answer. Makes the default safe. |
| **(c)** | One connection, scope-gated: raw tools require an `expert` scope on the token; without it the client sees only `prashna_ask`. | The enforcement mechanism for (b). |
| **(d)** | `prashna_ask` only; no raw tools. | Cleanest guarantee, but loses the drill surface the native uses daily. |

**Recommendation: (b) with (c) as the enforcement mechanism.** This adds a
third generated projection — **MCP-consult** — and makes profile selection an
entitlement question rather than an LLM's guess. A plain guest connecting the
MCP receives the consultation profile and **cannot** accidentally receive an
ungrounded reading, because the raw tools are not on their surface at all.

---

## §7 — Findings that must not be relitigated

These were established through investigation and reasoning in the originating
conversation. Re-deriving them wastes the session; challenging them requires
new evidence.

### §7.1 The three query paths are architecturally different

Only stages **auth**, **session pin**, and **registry dispatch → envelope** are
common to all three. Everything that makes the instrument *an instrument* —
planning, iteration, synthesis, gating — is ours in two paths and the client's
in one.

| Stage | Paripraśna | MCP raw tools | MCP `prashna_ask` |
|---|---|---|---|
| Conversation context | ours | none | none |
| Session pin | ✅ | ✅ | ✅ |
| **Planning → PlanReceipt** | ours | **client's LLM** | ours |
| **Agentic loop** | ours | **client's loop** | ours |
| Registry dispatch → v3 envelope | ✅ | ✅ | ✅ |
| **Synthesis into prose** | our model | **their model, invisible** | our model |
| **Pre-commit gates** | ✅ | **impossible** | ✅ |
| Persistence | ✅ | ❌ (D-05) | ❌ (D-05) |

**Raw-tools MCP is not "the same engine over a different transport."** It is
*"we expose our retrieval plane; someone else's brain uses it."*

### §7.2 The register guarantee cannot extend to raw-tools MCP

**This is the workstream's hardest constraint and its most important design
input.**

D-14 and the disclosure-tier architecture rest on a **pre-commit server-side
lint over prose crossing our boundary**. On the raw-tools path, **no prose
crosses our boundary.** The client's LLM receives internal-register envelopes
(`SIG.MSR.413`, `bodha_msr_signals`, `catalog_only`) and writes prose in
whatever register it likes, inside their client, invisibly. **We cannot lint
what we never see.**

Therefore:

- D-14 is deliverable on Paripraśna and `prashna_ask`.
- D-14 is **structurally undeliverable on raw tools.**
- **The envelope is the only defense on that path.**

This retroactively justifies the doctrine work: `judgment_flags`, honest
coverage with `total: null`, epistemic grades, `catalog_only_rows_present`, the
density contract. On our paths those are inputs to a gate we run. On the
raw-tools path they are the **entire** epistemic safety mechanism.

**The design consequence, and the workstream's central question:** the envelope
must be self-describing enough that a foreign LLM which reads it carefully gets
it right, and visibly flagged enough that one which reads it carelessly fails
*loudly* rather than silently. Consider whether reader-register labels (the
`register` block, §5/A-18) should ship *in the envelope* on this path, so a
foreign model has plain-language material to work from rather than only
internal ids.

### §7.3 The prediction ledger is channel-agnostic by necessity

A prediction confirmed from an MCP session must land in the same ledger and
surface in the same Samīkṣā queue as one from Paripraśna. So **one class of
durable memory is cross-channel regardless of D-05.**

Be precise: what D-05 dropped is **conversational transcript portability
only**. Do not let this workstream "simplify" the ledger's channel-agnosticism
away in D-05's name.

### §7.4 `prashna_ask` does not reopen DR-5

Adjudication DR-5 declined to make an in-product orchestrating LLM a
*doctrine-campaign deliverable*. The loop already exists in-product.
`prashna_ask` is a second door on it, not a new brain. This has been checked.

### §7.5 The 118-tool surface is too large for most clients and models

Not merely a model-context concern — Claude Desktop and ChatGPT connectors have
their own practical limits. The MCP-compact projection (~25–35 umbrellas +
`marsys_drill` dispatcher, with leaf tools reachable via envelope
`drill_pointers`) serves both constraints. **Kill the 45 aliases first**; they
double the confusion for every non-Claude model and waste context on every
client.

### §7.6 Known open defects in the current surface

| Item | Status |
|---|---|
| **CR-28** — `util_intent_classify` returns a **prompt**, not a classification. Three unreconciled intent implementations. | **FORMALLY OPEN.** Closes via the unified planner pipeline (engine-side). |
| `density_contract` covers 6 of ~118 capabilities. | Doctrine with 5% enforcement. A-05 makes the field mandatory. |
| v3 envelope is opt-in and defaults to legacy. | Flips only after the W4 answer-rubric battery passes. |
| Envelope is a hand-maintained two-process mirror; the codegen lane never landed. | Fixed by A-01 (monorepo + `@marsys/contract`). |
| Sidecar tools (`mimamsa_outcome`, `phala_event_anchors`) bypass the registry entirely. | Fixed by A-04 (mutation capability class). |
| Gate Ś item 8 (yoga-signal-class dasha eligibility) parked with evidence. | Carried forward from D-1.6. |
| An orchestrator state-commit race flagged as D-2's first agenda item. | Carried forward. |
| `server.ts` census comment is hand-maintained and has been recounted three times. | Reconciles to 118 today but is **not machine-generated**. Re-derive from a live `tools/list` if exact counts are load-bearing. |

---

## §8 — What good output from this workstream looks like

1. **OT-10 ruled**, with the projection set and the profile-selection mechanism
   fully specified.
2. **OT-2 and OT-5 ruled**, with their infrastructure consequences (job table
   or not; identity spine shape) drawn out.
3. **A projection-generation design**: how MCP-full, MCP-compact and
   MCP-consult are derived as pure functions of registry descriptors, and what
   descriptor metadata drives each.
4. **The `prashna_ask` contract**: signature — `prashna_ask(chart_id, question)`,
   no depth, no tier, per D-15 — plus cost cap, entitlement gating,
   progress/result shape, and failure modes.
5. **An envelope self-sufficiency design** answering §7.2 — what a foreign LLM
   must be able to read correctly with no gate of ours running.
6. **The alias cutover plan**: one breaking release, `notifications/tools/
   list_changed`, the 6 DEFERRED aliases resolved.
7. **MCP session semantics** under D-05, including whether OT-6 journaling
   exists.
8. Anything discovered that **contradicts or complicates** the parent
   architecture document — raised explicitly, not resolved silently.

### §8.1 Feeding results back

Rulings made in this workstream are recorded in
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §1 (moving the row out of §2) with
date and rationale, and the affected sections updated in the same edit. New
tensions go to its §18. New defects append to its §16 (append-only).

---

## §9 — Key file map

| Path | What |
|---|---|
| `platform-mcp/src/server.ts` | Imperative tool registration; census comment at 459–517 |
| `platform-mcp/src/tools/registry_bridge.ts` | The intended registry-backed registration path |
| `platform-mcp/src/tools/register_p1_aliases.ts` | The 45 aliases — to be deleted |
| `platform-mcp/src/tools/register_vidhi_plan.ts` | `plan_retrieval` |
| `platform-mcp/src/tools/intent_scope_classifier.ts` | DR-8 scope tuple producer |
| `platform-mcp/src/tools/reading_notes.ts` | Hardcoded to one chart |
| `platform-mcp/src/lib/envelope.ts` | **The hand-maintained mirror — to be deleted** |
| `platform-mcp/src/lib/response_budget.ts` | Structure-aware trimmer, `hardFloor` |
| `platform-mcp/src/lib/session.ts` | Session helper |
| `platform-mcp/src/oauth/` | Full OAuth 2.0 implementation |
| `platform/src/lib/retrieval/registry/types.ts` | `CapabilityDescriptor`, frozen D1 contract, `density_contract` |
| `platform/src/lib/retrieval/registry/chart_agnostic_gate.ts` | Build-time chart_id enforcement |
| `platform/src/lib/retrieval/registry/tool_name_bridge.ts` | Legacy→URI map + MCP whitelist |
| `platform/src/lib/retrieval/envelope.ts` | v3 envelope source of truth |
| `platform/src/lib/retrieval/session_pin.ts` | Build-provenance pin + drift detection |
| `platform/src/lib/vidhi/` | Compiler, registry_data, cr_status |
| `platform/src/app/api/retrieval/capability/route.ts` | The capability dispatcher — MCP's entry point |
| `platform/src/app/api/mcp/*` | session, sessions, keys, oauth, surface-spec, health, my/charts, authz |
| `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/` | D-1 / D-1.5 / D-1.6 briefs, binds, states, reports |
| `00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` | Parent architecture — read §1, §2, §4, §6, §8 |

---

## Appendix — PG-1 grounding-audit findings squarely for this workstream (2026-07-19)

The PG-1 wave (see `PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md`, `RETRIEVAL_SYSTEM_TRUTH_v1_0.md`)
surfaced several items owned by this MCP channel workstream. Pointers only:

- **`prashna_ask` does not exist** — `A-07` correction: grep across `platform/src` +
  `platform-mcp/src` returns **ZERO** hits (the apparent matches were the substring of
  the unrelated horary tool `prashna_undertaking_get`). "One agentic loop, two doors" is
  currently **one door** (web); the channel-agnostic second door is unbuilt. §18/T-2's
  "D-05 safe only if `prashna_ask` ships" is unmet. (`PG1-R3-0002`)
- **OT-10 (MCP profile selection)** stands; two new forks were added to the parent §2 that
  touch this channel: **OT-11** (which prediction ledger is canonical for NO-LEAKAGE —
  `mimamsa_predictions` populated vs `mcp_predictions` empty; `PG1-D3-0003`) and **OT-12**
  (P0' scope, `PG1-C2`).
- **Capability count baseline for the compact projection:** **119** registry URIs / **139**
  MCP tool names / **120** stale census — never 113 (`CAPABILITY_MANIFEST.json` is a
  governance-artifact catalog, not the MCP registry; `PG1-R1-0001..0003`). The
  MCP-compact "~25–35 umbrellas" count must derive from 119.
- **Live MCP defects to fix before the compact projection ships:** `phala_anchors_get` 422
  on optional `date_range` (F-25k), `ref_dignity_reference_get` 400 on `planet=Saturn`
  (F-25l), `drill_pointers` → `"unknown_tool"` on sidecar/alias tools (F-25j), three
  KEYSTONE sidecar tools double-encode their payload (F-25n, = the A-04 pull-in inventory),
  and `judgment_flags`/`coverage.total` are **v3-gated** — the default legacy envelope
  suppresses them (`PG1-R2-0007`/`-0008`).
- **Bearer-key MCP auth face returns 401** (`POST /mcp` with `Authorization: Bearer`) while
  the `?api_key=` seat is live — stale/rotated key or auth regression (F-25v, BIND B-3).

---

*End of MCP_CHANNEL_WORKSTREAM_HANDOFF v1.0 (2026-07-19) — PG-1 appendix added by Lane Z-1.*
