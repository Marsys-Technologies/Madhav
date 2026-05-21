---
artifact: CHAT_V2_FLAG_AUDIT_v1_0
canonical_id: CHAT_V2_FLAG_AUDIT
version: 1.0
status: DRAFT
authored: 2026-05-18
governing_brief: 00_ARCHITECTURE/chat_v2_briefs/round8/R8.E-flag-flips.md
governing_audit: 00_ARCHITECTURE/CHAT_V2_SURFACE_AUDIT_v1_0.md §3.7 + §3.8 + §3.9
changelog:
  - version: "1.0"
    date: 2026-05-18
    author: Claude (R8.E session)
    note: Initial authoring — per-flag recommendations for remaining dormant feature flags.
---

# CHAT V2 FLAG AUDIT v1.0

## §1 Mission

Per `CHAT_V2_SURFACE_AUDIT_v1_0.md §3.7 + §3.8 + §3.9`, multiple feature flags in
`platform/src/lib/config/feature_flags.ts` default to OFF in production despite their
code paths being fully built. This audit reviews each, classifies risk and impact, and
recommends **flip** vs **hold** vs **delete** for operator action.

This document is analysis-only. Each recommended flip becomes a separate small PR
(or a bundled PR for low-risk groups). Higher-risk decisions require native approval.

---

## §2 Flag inventory — post-R8.E baseline (2026-05-18)

### 2.1 Flipped in R8.E (this PR)

| Flag | Before | After | Rationale |
|---|---|---|---|
| `HISTORY_COMPRESSION_ENABLED` | `false` | `true` | Low-risk cost + latency optimization. Compresses oldest turns of conversations >32k tokens via a Haiku call before synthesis. No user-facing UX change. Operator-authorized for direct flip. |

### 2.2 Deleted in R8.E (this PR)

| Flag | Rationale |
|---|---|
| `MANIFEST_BUILDER_ENABLED` | Dead flag. Declared in `FeatureFlag` union and `DEFAULT_FLAGS` but had zero consumers anywhere in `platform/src/`. No code path activates or reads it. Pure dead-weight cleanup. |

---

### 2.3 Remaining dormant flags — operator follow-up required

#### Recommendations table

| Flag | Current default | Risk level | User-facing impact | Recommendation |
|---|---|---|---|---|
| `COST_VISIBILITY_FOR_USERS` | `false` | **Low** | Non-admin users see per-message cost breakdown in `PerMessageDetailsDrawer` | **FLIP** — after operator UX decision. The capability is built; the question is whether users should see cost figures. Operator decides. |
| `LLM_CHECKPOINTS_ENABLED` | `false` | **Medium** | Activates Phase 6 checkpoint guards (4.5, 5.5, 8.5 checkpoint gates in query pipeline) | **HOLD** — checkpoint family was Phase 6 safety infrastructure that never reached steady-state. Each sub-flag (`CHECKPOINT_4_5_ENABLED`, etc.) needs individual investigation before any flip. |
| `CHECKPOINT_4_5_ENABLED` | `false` | **Medium** | Per-checkpoint behavior, subordinate to `LLM_CHECKPOINTS_ENABLED` | **HOLD** — blocked on parent `LLM_CHECKPOINTS_ENABLED` decision. Do not flip independently. |
| `CHECKPOINT_5_5_ENABLED` | `false` | **Medium** | Per-checkpoint behavior | **HOLD** — same as above. |
| `CHECKPOINT_8_5_ENABLED` | `false` | **Medium** | Per-checkpoint behavior | **HOLD** — same as above. |
| `OBSERVATORY_ENABLED` (env-gated) | not set in `deploy.yml` | **Low** | Activates the entire Observatory dashboard for `super_admin` users only | **FLIP recommended** — super_admin tooling unblocked; no regular-user exposure. Set `MARSYS_FLAG_OBSERVATORY_ENABLED=true` in `deploy.yml` env_vars block + confirm Cloud Run env var. Phase O sealing artifact notes this as an AC.3/AC.4 follow-up item. |
| `SYNTHESIS_PROMPT_DEBUG` | `false` | **Low** | Verbose synthesis prompt debug logging | **HOLD** — flip locally for debugging sessions only. Never in production. |
| `DISCLOSURE_TIER_DEBUG` | `false` | **Low** | Verbose disclosure-tier debug logging | **HOLD** — same as above. |
| `BUNDLE_COMPOSER_DEBUG` | `false` | **Low** | Verbose bundle-composer debug logging | **HOLD** — same as above. |
| `PANEL_CHECKBOX_VISIBLE` | `false` | **Low** | Renders a UI checkbox for panel-mode opt-in | **INVESTIGATE** — panel mode itself is `PANEL_MODE_ENABLED: true`. Whether users should see an explicit opt-in checkbox is a UX decision. Audit what the checkbox currently looks like before deciding. |
| `PANEL_DEGRADE_2_OF_3` | `false` | **Medium** | Panel mode degrades from 3-LLM to 2-LLM response on failure | **HOLD** — panel mode is not the active workstream. Defer until panel mode is revisited. |

---

### 2.4 Already ON in production (no action needed)

Confirmed `true` in `DEFAULT_FLAGS` as of post-R8.E baseline:

`PANEL_MODE_ENABLED`, `VALIDATOR_FAILURE_HALT`, `AUDIT_VIEW_VISIBLE`,
`MANIFEST_QUERY_ENABLED`, `VECTOR_SEARCH_ENABLED`, `TRACE_ANALYTICS_ENABLED`,
`COST_TRACKING_ENABLED`, `CITATION_CHECK_ENABLED`, `HISTORY_COMPRESSION_ENABLED` (flipped R8.E),
all `DISCOVERY_*_ENABLED` flags, all `LL3_*_ENABLED` flags, `AUDIT_ENABLED`.

---

## §3 Operator decision queue

After this PR merges, the following decisions remain open:

- [ ] **COST_VISIBILITY_FOR_USERS** — flip or hold? (user-facing cost display). UX call required.
- [ ] **OBSERVATORY_ENABLED** — flip in `deploy.yml` + Cloud Run? (super_admin-only tooling). Low risk; recommended flip.
- [ ] **LLM_CHECKPOINTS family** — investigate per-checkpoint; defer until checkpoint scope is re-evaluated. Do not flip as a bundle.
- [ ] **PANEL_CHECKBOX_VISIBLE** — audit current UI, then decide.

Each decision yields a separate small PR or, if multiple low-risk flips are approved together, a bundled PR with explicit operator sign-off in the PR body.

---

## §4 How to read this document going forward

This document is a **point-in-time snapshot** at R8.E close. Future flag audits should:
1. Update §2.3 to reflect any flips, holds, or new flags added since.
2. Bump the version to `1.1` (minor: flag-state change) or `2.0` (major: structural change).
3. Record the change in the changelog frontmatter block.

*Authoring session: R8 Stream β (R8.E-flag-flips), 2026-05-18.*
