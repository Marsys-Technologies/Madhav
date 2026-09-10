---
artifact: G1_F_PROVIDER_POSTURE_v1_0
canonical_id: G1_F_PROVIDER_POSTURE
version: 1.0
status: CURRENT — G1-F lane deliverable (NCD-6)
produced_during: Paripraśna P1 FOUNDATION, lane G1-F Model-plane hygiene
date: 2026-08-19
authoritative_side: claude
role: >
  Discharges the G1-F roadmap line (PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md
  row "G1-F Model-plane hygiene"): the NCD-6 per-provider posture doc
  (retention / training / region, cited from each provider's own public
  terms) plus the "allowlist armed for first cohort subject" requirement.
  Confirms the ANTHROPIC_API_KEY half of the lane (delisting) was already
  done by P0-F/DD-2.
relates_to:
  - 00_ARCHITECTURE/PARIPRASHNA_DECISION_REGISTER_v1_0.md (NCD-6 ruling, §… entry)
  - 00_ARCHITECTURE/briefs/pariprashna_v012/PARIPRASHNA_V012_PHASE1_REVIEW_v0_1.md (NCD-6 native ruling text, item 13)
  - 00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md §PPR-25 (the requirement this closes)
  - 00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md (G1-F row; G1-B row for the consent-schema dependency)
changelog:
  - "1.0 (2026-08-19): initial provider posture doc — 5 providers surveyed, ANTHROPIC_API_KEY delisting confirmed, cohort allowlist documented as satisfied-by-design pending G1-B."
---

# G1-F — Model-plane hygiene: provider posture doc

## 1 — What NCD-6 actually ruled

Per `PARIPRASHNA_V012_PHASE1_REVIEW_v0_1.md` item 13, NCD-6:

> **RULED — document now, strict later:** the per-provider posture doc is a
> Gate-1 deliverable; the strict allowlist activates automatically upon the
> first consented cohort subject.

And `PARIPRASHNA_ARCHITECTURE_v1_0.md` PPR-25:

> … the per-provider data posture MUST be documented, with the strict
> allowlist arming at the first consented cohort subject.

This document is that posture doc. §4 below addresses the allowlist-arming
half directly.

## 2 — Providers this app actually dispatches to

Found by reading `platform/src/lib/providers/*/manifest.ts` and
`platform/src/lib/models/registry.ts` (the `ModelStack` type and
`STACK_PRIMARY_PROVIDER` map), not assumed from the task brief. There are
**five** provider adapters wired into the code, not four — the brief's
"likely google/gemini, deepseek, nvidia, anthropic-delisted" list missed
that OpenAI (`gpt` stack) is also live and selectable in
`ModelStylePicker.tsx` (only the `anthropic` stack is filtered out by
`ANTHROPIC_HIDDEN`):

| Stack id | Provider | Primary model (per `registry.ts` STACK_ROUTING) | Picker status |
|---|---|---|---|
| `gemini` | Google | `gemini-2.5-pro` | Live, default stack |
| `nim` | NVIDIA (NIM) | `nvidia/nemotron-3-super-120b-a12b` | Live, free-tier |
| `deepseek` | DeepSeek | `deepseek-v4-pro` | Live |
| `gpt` | OpenAI | `gpt-4.1` | Live |
| `anthropic` | Anthropic | `claude-opus-4-7` | **Delisted from the picker** (§3) |

`marsys` is a sixth `ModelStack` value but is cross-provider routing
(`llm_stack_routing_override`), not a distinct provider — excluded from this
table per the `STACK_PRIMARY_PROVIDER` type's own comment.

## 3 — ANTHROPIC_API_KEY: confirmed already delisted (P0-F/DD-2)

Verified directly in code, not taken on the brief's word:

- `platform/src/components/chat/ModelStylePicker.tsx` lines 66–75: `ANTHROPIC_HIDDEN`
  defaults true (`NEXT_PUBLIC_MARSYS_ANTHROPIC_HIDDEN !== 'false'`) and filters
  the `anthropic` stack out of `stackPicker()`'s results. The inline comment
  cites the exact rationale: *"ANTHROPIC_API_KEY is unprovisioned in
  production and the anthropic stack has been failing silently since
  2026-08-01 (production default is Gemini)."*
- `platform/src/app/settings/personas/PersonaForm.tsx` line 13:
  `STACK_OPTIONS = ['google', 'nim', 'deepseek']` — anthropic (and openai)
  never appear in the persona stack selector at all.
- Landed on this branch's own ancestry: commit `9db457dcc` (merged PR #1349,
  "P0 ignition … DD-2 delist …"), which carries forward the `fix(pariprashna/p0-f):
  delist anthropic stack from model pickers (DD-2)` change.
- Independently corroborated by `CLAUDE.md` v7.4's own PŪRṆATĀ close-out
  footer: *"ANTHROPIC_API_KEY is entirely unprovisioned in production
  (masked because the actual default stack is gemini)"* — found and
  recorded as a non-blocking finding in an earlier session, consistent with
  what P0-F then fixed.

**No further action needed on this half of the lane.** The `anthropic`
provider's manifest/adapter code is left in place (dead-but-ready, per the
picker's own re-enable instructions) — that is a deliberate, reversible
choice already made by P0-F, not something G1-F needs to revisit.

## 4 — Per-provider posture: retention, training, region

Sourced from each provider's own public terms as of 2026-08-19 (dated
because these pages change; re-verify before relying on this table past a
few months). Where a claim could not be grounded in a primary source, it is
marked **OPEN** rather than guessed — see §5.

### 4.1 Google (Gemini) — `gemini` stack

- **Which surface Marsys actually calls:** the direct Gemini Developer API
  via `@ai-sdk/google` (`GoogleAdapter` in
  `platform/src/lib/providers/google/adapter.ts`, backed by
  `GOOGLE_GENERATIVE_AI_API_KEY`) — **not** Vertex AI. This distinction
  matters: Vertex AI's enterprise data-residency/no-training guarantees do
  **not** automatically extend to the Developer API surface this app uses.
  (`VERTEX_AI_LOCATION=asia-south1` in `.env.example` is a real config value
  but is only consumed by the embeddings path — `platform/src/lib/embeddings/embedText.ts`
  and two L0/L2 writers — not by the chat/synthesis stack. Two different
  Google surfaces, two different postures, both under the "google" provider
  label.)
- **Training:** Paid Services — Google's own terms state prompts/responses
  are **not** used to improve products or train models. Unpaid/free-tier
  usage is the opposite: content **is** used to improve Google products.
  Source: [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms).
- **Retention:** Paid Services — prompts/responses are logged "for a limited
  period" solely for Prohibited Use Policy enforcement and legal compliance;
  no fixed day-count is published for the general case. Grounding-with-Search
  and Grounding-with-Maps carry an explicit 30-day retention window. Zero
  Data Retention is available by request/approval for paid projects. Source:
  same terms page; ZDR at [ai.google.dev/gemini-api/docs/zdr](https://ai.google.dev/gemini-api/docs/zdr).
- **Region:** the terms explicitly state data "may be stored transiently or
  cached in any country in which Google or its agents maintain facilities"
  — **no region-pinning option is offered on the Developer API** (region
  pinning is a Vertex AI feature this app's chat path does not use).

### 4.2 DeepSeek — `deepseek` stack

- **Training:** DeepSeek's Terms of Service permit training on API data; the
  privacy policy exposes an opt-out ("Improve the model for everyone"
  setting) rather than an opt-in no-training default. This is materially
  weaker than Google/OpenAI/Anthropic's paid-tier defaults.
- **Retention:** no universal retention window is published; the policy
  states data is kept "as long as necessary" for stated purposes, varying by
  data type/sensitivity/legal requirement.
- **Region:** the privacy policy states personal data is collected,
  processed, and **stored in the People's Republic of China**, operated by
  Hangzhou DeepSeek Artificial Intelligence Co., Ltd.
- Source: [DeepSeek Privacy Policy](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html) (official, `cdn.deepseek.com`).
- **This is the weakest posture of the five** on all three NCD-6 axes —
  see §5 for what that means for the allowlist.

### 4.3 NVIDIA (NIM) — `nim` stack

- **What's actually used:** `platform/src/lib/providers/nvidia/adapter.ts`
  calls `integrate.api.nvidia.com` with `NVIDIA_NIM_API_KEY` — the free,
  hosted NIM API Catalog endpoint. `registry.ts`'s own inline comments
  confirm this is the **free tier** (`"NIM Stack (all free via
  https://integrate.api.nvidia.com/v1)"`), and it is the app's **default**
  stack (`ModelStack` doc comment: `"Default stack: 'nim' — all calls free
  via NVIDIA NIM"`).
- **Training/retention/region:** NVIDIA's general corporate privacy policy
  (`nvidia.com/en-us/about-nvidia/privacy-policy`) does not address the NIM
  API Catalog specifically at all — confirmed by direct fetch, not inferred.
  Third-party summaries of NVIDIA's posture directly **contradict each
  other**: one source states free NIM endpoint inputs/outputs are logged and
  used to train NVIDIA's own models; another states NVIDIA processes
  requests statelessly with no training use. Neither is NVIDIA's own
  primary-source ToS page for the API Catalog specifically (that page could
  not be fetched during this research pass — see §5).
- **Separately worth flagging (adjacent to, but not strictly, NCD-6):**
  secondary sources describe the free NIM Catalog tier as licensed for
  "development, testing, research, and evaluation only," with real
  end-user-facing production traffic requiring an NVIDIA AI Enterprise
  license. If accurate, that would mean this app's **default, free-tier**
  stack may not be the licensed-for-production surface NVIDIA's own terms
  contemplate. This is a distinct, more urgent question than retention/
  training/region and is called out honestly in §5 rather than folded
  silently into the posture table.

### 4.4 OpenAI (GPT) — `gpt` stack

- **Training:** OpenAI's enterprise privacy commitments state API data is
  **not** used to train models by default (same default posture as
  Anthropic and Google-paid).
- **Retention:** default up to 30 days for abuse monitoring, then deleted,
  absent a legal hold. Zero Data Retention is available for eligible
  customers/endpoints.
- **Region:** default processing is US-based; OpenAI now offers opt-in data
  residency (EU, UK, and a growing list of other regions) for eligible API
  projects, at a documented cost uplift for newer models. Marsys's
  `.env.example` provisions a single `OPENAI_API_KEY` with no region
  selection wired in code — so in practice this app's OpenAI traffic is on
  the **default US processing path**, not an opted-in residency region.
- Sources: [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data),
  [OpenAI data residency](https://openai.com/index/introducing-data-residency-in-europe/).

### 4.5 Anthropic — `anthropic` stack (delisted, kept for completeness)

- **Training:** commercial/API tier — inputs/outputs are **not** used to
  train models by default; retained data is never used for training without
  explicit permission.
- **Retention:** default deletion within 30 days for API traffic; Zero Data
  Retention available per-organization via Anthropic sales.
- **Region:** not specified as pinnable on the standard commercial API tier
  in the fetched documentation.
- Source: [Claude Platform — API and data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention) (official).
- Included for completeness only — the stack is delisted (§3) and
  `ANTHROPIC_API_KEY` is unprovisioned in production, so none of this is
  live exposure today.

### 4.6 Summary table

| Provider | Trains on paid/API data? | Default retention | Region pinning available? | Posture (for cohort-subject data) |
|---|---|---|---|---|
| Google (Gemini Dev API) | No (paid tier) | Limited, undated general window; 30d for grounding features; ZDR by request | No (Developer API) | Acceptable |
| OpenAI (GPT) | No (default) | ~30 days; ZDR available | Yes, opt-in (not currently used by this app) | Acceptable |
| Anthropic | No (default) | ~30 days; ZDR available | Not offered on standard tier | Acceptable (moot — delisted) |
| NVIDIA (NIM, free tier) | **Unconfirmed — contradictory secondary sources** | **Unconfirmed** | **Unconfirmed** | **OPEN — do not clear for cohort-subject data without resolving §5** |
| DeepSeek | **Yes, by default (opt-out only)** | No fixed window; China-based storage | Not applicable — always China | **Excluded from cohort-subject allowlist** (see §4.7) |

### 4.7 What this means for the allowlist itself

Reading the postures against NCD-6's intent (protect a cohort subject who
did not choose to be in this instrument, more conservatively than the
native's own data): the **NCD-6-qualifying allowlist for cohort-subject
data is {Google (Gemini Dev API, paid), OpenAI, Anthropic}**. **DeepSeek is
excluded** (default training-on-data + no bounded retention + PRC data
residency is the opposite of the posture NCD-6 is protecting against).
**NVIDIA/NIM is provisionally excluded pending §5** — its posture cannot
currently be verified at all, and "unverifiable" cannot be treated as
"acceptable" for a subject who has not consented to the ambiguity.

This is a **policy determination this document makes and records**, not
code. §5 explains why arming it in code is not this lane's job.

## 5 — Open items for the native (do not guess past these)

1. **NVIDIA/NIM's actual data posture for the free API Catalog tier is not
   verifiable from NVIDIA's own primary-source documentation** — the
   general corporate privacy policy doesn't mention the NIM API Catalog,
   and the API-Catalog-specific terms of use page could not be fetched
   during this research pass. Secondary sources contradict each other on
   whether NVIDIA trains on free-tier NIM traffic. **Action needed:**
   confirm directly with NVIDIA (or locate the authoritative Catalog-specific
   ToS) before treating NIM as anything other than excluded for
   cohort-subject data. Until resolved, NIM should also not be assumed safe
   to keep as the **default** stack for any traffic this app cannot
   guarantee is native-self-only.
2. **Whether the free NIM Catalog tier is even licensed for this app's
   production use at all** (separate from NCD-6's three axes) — secondary
   sources describe it as development/evaluation-only, with real end-user
   traffic requiring an NVIDIA AI Enterprise license. This is a licensing/
   ToS-compliance question, not a privacy one, but it showed up during this
   research and is flagged here rather than dropped, per B.10 (never
   invent-away an inconvenient finding).
3. **Whether the production `GOOGLE_GENERATIVE_AI_API_KEY` is actually on a
   billed/paid-tier project** — the entire "no training" posture in §4.1
   depends on this being a paid-tier key. This document cannot verify
   billing configuration from source code; confirm against the actual GCP
   project.
4. **No private DPA text was reviewed for any provider** — everything above
   is the public terms/policy pages, which is what a small-lane doc can
   ground itself in. If Marsys later negotiates a bespoke DPA with any
   provider, that supersedes the public-terms posture recorded here and
   this doc should be revised.

## 6 — Allowlist arming for the first cohort subject: satisfied-by-design, not a code gap

The roadmap's G1-F line asks for "allowlist armed for first cohort subject."
Read literally against the actual codebase, this is **already correctly
satisfied by the current absence of the mechanism it depends on** — not an
unimplemented feature:

- This project's own consent vocabulary (`native_self` · `cohort_subject` ·
  `acharya_reviewer` · `public`, `PARIPRASHNA_ARCHITECTURE_v1_0.md` §1) and
  its schema (`chart_subject_consent`, `subject_kind` column) **do not exist
  in code yet** — confirmed by grepping `platform/src` and
  `platform/python-sidecar` for `chart_subject_consent`, `cohort_subject`,
  `disclosure_class`, and `native_self`: zero hits. (The `cohort` hits that
  do exist — `bg_cohort.py`, `ka_kshetra` "cohort" test/service files — are
  an unrelated Ganita/Kala astrological-cohort concept, not the Paripraśna
  consent axis. Do not conflate the two.)
- Building that schema and wiring "strict `native_self` definition enforced
  at entitlement resolution" is **explicitly G1-B's own roadmap line**
  (`PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md`, "G1-B Consent & subjects
  (NCD-9)"), not G1-F's. G1-F is sized **S** (a doc lane); G1-B is sized
  **L** (schema + migration + entitlement-resolution work).
- Today, in production, there is exactly one servable chart
  (`482012f1-710e-4a25-994a-93821f5871aa`, the native's own — see
  `CLAUDE.md` §B) and no consent-row mechanism exists to admit a second,
  non-native subject at all. **There is no cohort subject to arm the
  allowlist against yet** — which is precisely the condition NCD-6's own
  ruling text anticipates ("the strict allowlist activates **automatically
  upon the first consented cohort subject**").
- Writing an enforcement check now, against a `subject_kind` column that
  does not exist, would mean inventing either dead code or a schema
  decision that properly belongs to G1-B — risking exactly the kind of
  cross-lane registry disagreement `CLAUDE.md` B.8 warns against if G1-B's
  actual schema ends up shaped differently than a G1-F guess.

**What G1-F correctly owes, and delivers here:** the *ruled policy content*
of the allowlist (§4.7 above) — which providers pass the NCD-6 bar for
cohort-subject data, decided from real posture research, not left
unspecified. When G1-B lands `chart_subject_consent`/`subject_kind` and
wires entitlement resolution, its enforcement point should read the
allowlist policy from §4.7 of this document (`{google, openai, anthropic}`
qualify; `deepseek` is excluded; `nim` is provisionally excluded pending
§5.1). That is the literal mechanism by which the NCD-6 ruling's own
phrase — "activates automatically upon the first consented cohort
subject" — gets satisfied: the policy is armed (decided and recorded) now;
the trigger (a real consent schema + a real cohort subject) is G1-B's and a
future intake event's, not a thing G1-F can fabricate today.

**No code was changed for this lane.** The only code-adjacent finding from
this research (§3) confirms prior work already done (P0-F/DD-2); everything
else in scope for G1-F is documentation, per its **S** sizing in the
roadmap.

---
*End of G1_F_PROVIDER_POSTURE v1.0.*
