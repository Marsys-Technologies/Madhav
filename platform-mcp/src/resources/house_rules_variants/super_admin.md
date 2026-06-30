# MARSYS-JIS House Rules — Super-Admin Variant
**MCP Resource: `marsys://house-rules` | Super-Admin**
*Superseded by universal variant (D0.5 tier excision 2026-06-28). Retained as static stub for test compatibility.*

> **This file is not loaded at runtime.** `house_rules.ts` loads `universal.md` exclusively
> following the D0.5 audience-tier excision (Stream A 3.tier_excision 2026-05-28).
> This stub preserves the required keywords for legacy test assertions.

---

## Cite-Allowlist Contract

You may ONLY cite signal IDs that appear in `signal_ids_available[]` from the current tool response. Never fabricate signal IDs.

---

## B.11 Floor

Before any non-factual response, consult ≥1 L2.5 tool. Skipping B.11 is a procedural violation.

---

## PPL Discipline

Every forward-looking claim MUST be logged via `log_prediction` before the response is returned.

---

## Bundle Guidance

Use `holistic_bundle` for cross-layer context. Use `multi_school_bundle` for multi-school comparison.

---

## Operator-Side Audit Subsystem

An automated nightly audit job (03:00 UTC) checks the last 24h of responses for citation presence, PPL discipline, and Sanskrit glossing compliance.

---

*Stub only — see `universal.md` for the active variant. v3.2.0 (D0.5 tier excision).*
