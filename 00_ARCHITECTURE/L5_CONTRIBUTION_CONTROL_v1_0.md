---
artifact: L5_CONTRIBUTION_CONTROL_v1_0.md
canonical_id: L5_CONTRIBUTION_CONTROL
version: 1.0
status: DRAFT — backbone architecture for user-facing control of L5 Mīmāṃsā's influence on responses
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  Defines the framework by which the USER controls how much L5 Mīmāṃsā influences any given response —
  independently per contribution channel, identically across the internal portal and the MCP channel.
  The engine ALWAYS computes; the toggles govern APPLICATION/SURFACING at serve time. Native-ruled
  2026-06-22. This is a backbone concern (serve-time + portal + MCP + response envelope), not an L5
  internal detail — hence its own artifact, referenced by L5_MIMAMSA_VISION + CAMPAIGN_PLAN.
native_decisions:
  - "Extensible channel framework; 2 channels lit now (LEL-citation, learning-influence)"
  - "Default = BOTH ON (full-power); user opts OUT"
  - "Scope = per-request override + saved user default"
  - "Transparency = silent suppression + queryable metadata (clean output, full audit)"
  - "Must work identically via internal portal AND MCP (parity-gated)"
depends_on_artifacts:
  - L5_MIMAMSA_VISION_v1_0.md (Pillar 1 SCORE / Pillar 4 FEED-BACK — the channels being gated)
  - retrieval registry + parity_check.ts (the seam that guarantees portal/MCP parity)
---

# L5 Contribution Control — User Governance of the Learning Layer's Influence

> *The native must be able to ask the chart a question and choose, per question, whether the
> instrument answers as a **pure classical reading** or as a **calibration-enhanced reading** — and
> whether the answer **cites their lived events** or not. The engine always computes everything; the
> user decides what reaches the page.*

---

## §1 — The core principle: COMPUTE ALWAYS, APPLY ON DEMAND

This is the one idea the whole framework rests on, and it must be honored everywhere:

- **L5 always runs.** Calibration is computed, attribution is traced, multipliers are derived, the LEL
  is logged and matched. Nothing about the toggles stops L5 from doing its work or writing its tables.
- **The toggles act at SERVE TIME, not BUILD TIME.** They govern whether L5's *already-computed*
  outputs are **applied to** / **surfaced in** a given response. Turning a channel off subtracts an
  influence from the answer; it never makes the engine compute less.

Why this separation matters: it keeps the audit trail complete (every score exists and is inspectable
regardless of toggle state), it makes toggles instant and reversible (no rebuild), and it means a user
flipping "learning OFF" still leaves a fully-populated calibration record they can inspect later.

---

## §2 — The contribution channels (extensible registry; 2 lit now)

L5 influences a response through distinct **contribution channels**. Each is an independently
switchable unit registered in a **channel registry** (so new channels slot in without re-architecting).
Two are lit at v1; the registry is built to hold more.

| channel_id | layman name | what it does to a response | OFF behavior | ON behavior (default) |
|---|---|---|---|---|
| `lel_citation` | "Cite my life events" | LEL facts are quoted/referenced *in the response text* as grounding evidence | No lived-event facts appear in the answer; pure chart reading | Reading is grounded with the native's actual logged events |
| `learning_influence` | "Apply adaptive learning" | L5's calibration/attribution **multipliers** silently reshape confidences + weights (the reverse channel: damps `ph_nimitta`, re-weights signals/edges) | **Pure classical reading/prediction** — L1–L4 output with ZERO adaptive modulation | Calibration-enhanced output (empirical track-record modulates confidences) |

**Future channels (registry-ready, not lit at v1)** — e.g. `remedy_adaptation` (learned remedy
efficacy modulating RM prescriptions), `discovery_prior_shaping` (LL.7 priors influencing discovery
surfacing), `prompt_adaptation` (LL.4 learned prompts). Each future channel is one registry row + one
serve-time application point; no framework change.

**Independence is the point.** A user can cite LEL facts while keeping learning off (grounded but
classical), or apply learning while suppressing LEL citation (enhanced but no event facts shown). The
channels never imply each other.

---

## §3 — Default, scope, and resolution

**Default (out-of-the-box): BOTH ON.** A user who sets nothing gets the instrument at full power — LEL
cited + learning applied. Users opt *out* of channels they don't want.

**Scope: per-request override on top of a saved user default.** Resolution order for each channel, per
request:

```
1. explicit per-request value (portal toggle for this query / MCP tool arg for this call)   ← wins
2. else the user's saved default preference (persisted per user)
3. else the system default (ON)                                                              ← fallback
```

So a user can keep `learning_influence` off as their saved default (they usually want pure reading) yet
flip it ON for a single "let me check accuracy" query — without changing their default.

**Persistence:** saved defaults live in a per-user preference store (one row per user × channel). The
per-request override is transient (request-scoped), never mutates the saved default.

---

## §4 — One definition, two channels: the parity seam

The framework MUST behave identically through the internal portal and through MCP. The codebase already
has the seam that guarantees this: the **canonical retrieval registry** with a CI **parity gate**
(`parity_check.ts` throws on any portal/MCP capability mismatch; `mcp_capability_bridge.ts` maps MCP
tool names ↔ `marsys://` URIs). The contribution-control framework rides this seam:

- **Define once** — the channel registry + the resolution logic live in one shared module in the
  retrieval registry (not duplicated in portal or MCP code).
- **Portal consumes it** — the Consume-Chat / portal request path reads per-request toggles from the
  UI and passes them into the shared resolver.
- **MCP consumes it** — each relevant MCP tool exposes the toggles as **optional tool arguments**
  (e.g. `lel_citation: bool`, `learning_influence: bool`); absent → saved default → system default.
- **Parity-gated** — the parity check is extended to assert both channels expose the same contribution
  controls. A portal toggle with no MCP equivalent (or vice versa) **fails CI**. This is how "works
  the same in both" becomes a guarantee, not a hope.

```
            ┌──────────────── shared contribution-control module (retrieval registry) ───────────────┐
            │   channel registry  ·  resolution(per-request → saved → system)  ·  serve-time gate     │
            └───────────────▲───────────────────────────────────────────────▲────────────────────────┘
                            │                                                │
                 portal request path                                  MCP tool args
                 (UI toggles per query)                        (lel_citation?, learning_influence?)
                            │                                                │
                            └───────────────── parity_check.ts (CI gate) ────┘   ← throws on mismatch
```

---

## §5 — Where each channel is APPLIED at serve time (the gate points)

The Whole-Chart-Read (B.11) pipeline composes a response from all layers. L5 contribution control adds
**gate points** where an L5 influence is conditionally applied:

- **`lel_citation` gate** — at response composition, where LEL evidence would be woven into the text
  (e.g. `ph_phaladesa`/synthesis narration). OFF → the composer omits LEL fact citations; the reading
  stands on chart structure alone. ON → LEL facts are cited inline.
- **`learning_influence` gate** — at the point where L5 overlay multipliers would modulate
  confidences/weights across L1–L4. OFF → the pipeline uses the **un-modulated classical base values**
  (the raw L1–L4 output, since the base is never mutated). ON → the **effective values** (base joined
  with the L5 overlay). The full propagation mechanism — which assets are touched (L1→L4, never L0),
  how the deterministic base stays segregated from the adapted value, and how a single correction is
  applied exactly once across the `bodha_msr_signals` fan-out without double-counting — is specified in
  **`L5_LEARNING_PROPAGATION_v1_0.md`**. This `learning_influence` toggle is the single master switch
  that subtracts that entire overlay cleanly at every layer.

Critically, with `learning_influence` OFF the response is **byte-for-byte the pure classical reading**
— the L5 modulation is simply not applied. This is what makes "pure reading mode" trustworthy: it is
literally L1–L4 with L5 subtracted, not "L5 with a small weight."

---

## §6 — Transparency: silent suppression + queryable metadata

Per native ruling, OFF channels are **silent in the response body** (no "learning layer is off" line
cluttering the reading). But the instrument's audit discipline (CLAUDE.md B.11) is preserved by
**response metadata**:

- Every response carries a `contribution_state` block in its metadata (not its prose): which channels
  were ON/OFF for this response, and how each value was resolved (per-request / saved-default / system).
- An optional **"why / provenance" endpoint** (and MCP equivalent) lets a user ask, after the fact,
  "what was active when you answered that?" and "what would have changed with learning on?" — surfacing
  the always-computed L5 record that the toggle suppressed.

This gives clean reading-grade output AND full auditability: nothing is hidden from inspection, it's
just not forced into the prose.

> **Optional future nicety (not v1):** a user-configurable preference to show a one-line mode banner.
> The metadata channel-state is the v1 contract; the banner is a later opt-in.

---

## §7 — Honesty interaction (why this framework strengthens, not weakens, L5)

This control framework is not a hedge against L5 being wrong — it is consistent with L5's n=1 honesty
discipline (VISION §4):

- With `learning_influence` OFF, the user gets the classical instrument with its honest
  structural-not-yet-empirical confidence (the L4 D5 stance) — no claim that empirical calibration has
  improved anything.
- With it ON, the user opts into the calibration-enhanced view, and the metadata can carry the n +
  leakage-status behind the modulation (so "enhanced" is never a black box).
- The default-ON stance is defensible precisely because the metadata keeps the enhancement auditable
  and the OFF switch is always one request away.

---

## §8 — Build implications (folds into the L5 campaign)

This framework is part of the L5 backbone and is built within the L5 campaign (see
`L5_MIMAMSA_CAMPAIGN_PLAN_v1_0.md`, new Phase P5.5). Concretely:

1. **Channel registry + resolver** — shared module in the retrieval registry; the channel registry
   row shape `{channel_id, layman_name, default_state, apply_point}`.
2. **Preference store** — per-user × channel saved defaults (migration; next free number at build open).
3. **Serve-time gate points** — wire the two gates (§5) into the Whole-Chart-Read composition + the L5
   reverse-channel application. The `learning_influence` OFF path MUST yield the un-modulated L1–L4
   values (verifiable: OFF output == pre-L5 baseline).
4. **Portal controls** — per-query toggles in the reading UI + a settings surface for saved defaults.
5. **MCP tool args** — optional `lel_citation` / `learning_influence` args on the relevant tools,
   resolving through the same shared resolver.
6. **`contribution_state` response metadata** + the optional provenance endpoint.
7. **Parity-gate extension** — `parity_check.ts` asserts both channels expose identical controls (CI).
8. **Tests** — OFF==baseline equality test for `learning_influence`; LEL-absent test for `lel_citation`
   OFF; per-request-over-saved-default resolution test; portal/MCP parity test.

**Constraints inherited:** deterministic application (the gate is a deterministic switch, not an LLM
decision); no audience tier (this is user preference, NOT a gating/permission tier — every user has
every channel); L-is-authority (OFF path uses the real un-modulated upstream values, never a fabricated
substitute).

---

## §9 — Open sub-decisions for native (small; don't block the vision)

| # | Decision | Cowork lean |
|---|---|---|
| **C1** | Are toggles ever exposed per-DOMAIN (e.g. learning on for career, off for health) or global-per-request only? | Global-per-request at v1; per-domain is a later registry extension |
| **C2** | Does the MCP expose toggles as per-tool args, or one "session preferences" tool that sets them for subsequent calls? | Per-tool optional args (stateless, parity-clean) + optionally a prefs tool later |
| **C3** | Should `lel_citation` OFF also suppress LEL-derived *paraphrase* (not just direct citation), or only literal event facts? | Suppress literal event facts at v1; define paraphrase handling during build |

---

*End of L5_CONTRIBUTION_CONTROL v1.0. The user governs how much L5 influences each response, per channel,
identically across portal + MCP. Compute-always / apply-at-serve-time; extensible channel registry with
LEL-citation + learning-influence lit; default both ON with per-request override over saved default;
silent suppression with queryable metadata; parity-gated so the two channels can never diverge.*
