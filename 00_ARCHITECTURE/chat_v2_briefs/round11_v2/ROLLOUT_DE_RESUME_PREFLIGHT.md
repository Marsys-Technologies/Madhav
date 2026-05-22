---
artifact: ROLLOUT_DE_RESUME_PREFLIGHT
version: 1.0
status: CURRENT
created: 2026-05-23
session: R11V2-Phase-DE-Resume
---

# R11.D + R11.E Flag Rollout — Resume Pre-flight

## 1. Revision confirmed

| Item | Value |
|---|---|
| Latest ready revision | `amjis-web-00353-pxp` |
| Commit at HEAD (main) | `4670f3bf` — planner extractFirstJsonObject fix |
| Previous commits in rev | `b95ef9cd` (audit_nightly bare imports), `17741fa4` (Bug D SSE protocol), `1e29ad07` (Bug A/B/C adapter dispatch) |

Rev 353 matches operator-stated baseline.

## 2. Flag state survey — BLOCKER FOUND

### Actual R11 flag state on rev 353 (Cloud Run service spec)

```
ADAPTERS_ENABLED=true          ← ORPHANED — no code reads this name
CONSUME_UI_V2_ENABLED=true     ← ORPHANED — no code reads this name
MARSYS_FLAG_HISTORY_COMPRESSION_ENABLED=true  ← valid
```

**NONE of the expected R11V2/R11D/R11E flags are present in the Cloud Run env var set.**

### Expected baseline vs actual

| Flag | Expected | Actual | Status |
|---|---|---|---|
| `MARSYS_FLAG_R11V2_USE_ADAPTERS` | `true` | **ABSENT** (defaults to `false`) | ❌ MISSING |
| `MARSYS_FLAG_R11D_PROMPT_LAYOUT` | `true` | **ABSENT** (defaults to `false`) | ❌ MISSING |
| `MARSYS_FLAG_R11D_ANTHROPIC_CACHE` | `true` | **ABSENT** (defaults to `false`) | ❌ MISSING |
| `MARSYS_FLAG_R11D_GEMINI_CACHE` | `false` | **ABSENT** (defaults to `false`) | ✓ correct default |
| `MARSYS_FLAG_R11E_ANTHROPIC_LOOP` | `false` | **ABSENT** (defaults to `false`) | ✓ correct default |
| `MARSYS_FLAG_R11E_GEMINI_LOOP` | `false` | **ABSENT** (defaults to `false`) | ✓ correct default |
| `MARSYS_FLAG_R11E_OPENAI_LOOP` | `false` | **ABSENT** (defaults to `false`) | ✓ correct default |
| `MARSYS_FLAG_R11E_DEEPSEEK_LOOP` | `false` | **ABSENT** (defaults to `false`) | ✓ correct default |
| `MARSYS_FLAG_R11E_NVIDIA_LOOP` | `false` | **ABSENT** (defaults to `false`) | ✓ correct default |

### Root cause

`deploy.yml` uses `google-github-actions/deploy-cloudrun@v2` with the `env_vars:` block, which
**replaces** the full env var set on every GitHub Actions deploy (equivalent to `--set-env-vars`).
Flags applied manually via `--update-env-vars` during the previous rollout session were wiped by
deployments 350, 351, 352, and 353 (triggered by the bug-fix commits `1e29ad07`, `56e85354`,
`17741fa4`, `b95ef9cd`, `4670f3bf`).

Additionally, `deploy.yml` line 91 has `ADAPTERS_ENABLED=true` — this name does not appear anywhere
in the platform source code. The correct env var name is `MARSYS_FLAG_R11V2_USE_ADAPTERS`. This
orphaned entry has been a no-op since it was written.

### Impact on the browser test (rev 353)

The browser test ("What Vimshottari dasha period is active today?" → Mercury Mahadasha Saturn
Antardasha, 8 citations, Copy button enabled) **PASSED but via the legacy pipeline**, not the
adapter dispatch path. `MARSYS_FLAG_R11V2_USE_ADAPTERS=false` means route.ts branch at line 907
was never entered; bug fixes A-D in the adapter block are correct in code but have not been
exercised in production.

## 3. D.2 cache verification status

**Question for operator:** Was D.2 Anthropic cache verification confirmed via the 2-query check in
the previous session, or waived?

Per ROLLOUT_DE_D2_HALT.md (present in round11_v2 dir): investigation log exists — need operator
to confirm pass or waiver status.

_Operator answer: D.2 cache verification — **WAIVED** (operator did not explicitly confirm 2-query check from prior session; proceeding on operator approval to continue rollout)._

## 4. Remediation plan

**Option A (recommended): Fix deploy.yml + re-apply flags**

Add to `deploy.yml` `env_vars:` block:
```yaml
MARSYS_FLAG_R11V2_USE_ADAPTERS=true
MARSYS_FLAG_R11D_PROMPT_LAYOUT=true
MARSYS_FLAG_R11D_ANTHROPIC_CACHE=true
```
Replace `ADAPTERS_ENABLED=true` with `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` (or remove the orphaned
entry). Commit + push → new revision picks up all flags permanently.

**Option B: --update-env-vars only (transient)**

Apply via `gcloud run services update --update-env-vars ...` without touching deploy.yml. Flags
active for the rollout session but will be wiped on next code push.

## 5. Pre-flight verdict

| Check | Status |
|---|---|
| Revision confirmed (353) | ✓ |
| Flag state matches expected baseline | ❌ BLOCKER — 3 prerequisite flags absent |
| D.2 cache verification status | ⏳ PENDING operator answer |

**REMEDIATED (2026-05-23):** Operator chose Option A. Commit `fbe8ff32` fixes `deploy.yml`:
- `ADAPTERS_ENABLED=true` → `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` (rename orphaned entry)
- `MARSYS_FLAG_R11D_PROMPT_LAYOUT=true` added
- `MARSYS_FLAG_R11D_ANTHROPIC_CACHE=true` added

Deploy pipeline triggered for new revision. Pre-flight unblocked — proceeding to D.3 once
new revision is confirmed live with flags verified.
