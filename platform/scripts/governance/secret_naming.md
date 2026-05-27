# Secret Manager naming — current state + remediation note

> Authored by unit **0b.2 — Secret + DB-password remediation** (Stream B).
> Status: **DOCUMENTATION ONLY**. No prod renames performed.
> Renames touch live infra and belong to a later operations wave with
> a controlled cutover (env-var publishers + Cloud Run revisions must
> change in lockstep).

## §1 — Current naming in GCP Secret Manager

Discovered via `grep` over `.github/workflows/`, `platform/cloudbuild*.yaml`,
`platform-mcp/cloudbuild.yaml`, plus `00_ARCHITECTURE/**` historical refs.
This is the live, in-use set of secret IDs as of unit 0b.2:

| Secret ID                          | Style          | Bound env var                       | Bootstrap surface                       |
|------------------------------------|----------------|-------------------------------------|-----------------------------------------|
| `amjis-db-password`                | kebab-lower    | `DB_PASSWORD`                       | `.github/workflows/deploy.yml`          |
| `openai-api-key`                   | kebab-lower    | `OPENAI_API_KEY`                    | `.github/workflows/deploy.yml`          |
| `mcp-internal-token`               | kebab-lower    | `MCP_INTERNAL_TOKEN`                | `platform-mcp/cloudbuild.yaml`          |
| `amjis-voyage-api-key`             | kebab-lower    | (historical; possibly retired)      | `00_ARCHITECTURE/BRIEFS/MASTER_AUDIT_BRIEF_v1_0.md` |
| `ANTHROPIC_API_KEY`                | UPPER_SNAKE    | `ANTHROPIC_API_KEY`                 | `.github/workflows/deploy.yml`          |
| `GOOGLE_GENERATIVE_AI_API_KEY`     | UPPER_SNAKE    | `GOOGLE_GENERATIVE_AI_API_KEY`      | `.github/workflows/deploy.yml`          |
| `DEEPSEEK_API_KEY`                 | UPPER_SNAKE    | `DEEPSEEK_API_KEY`                  | `.github/workflows/deploy.yml`          |
| `NVIDIA_NIM_API_KEY`               | UPPER_SNAKE    | `NVIDIA_NIM_API_KEY`                | `.github/workflows/deploy.yml`          |
| `PYTHON_SIDECAR_API_KEY`           | UPPER_SNAKE    | `PYTHON_SIDECAR_API_KEY`            | `.github/workflows/deploy.yml`          |

### §1.1 — Historical confusion (already resolved)

The canonical DB secret is `amjis-db-password`. **Not** `amjis-app-db-password`
(an older draft name that lived only in early M2 briefs). Multiple
`00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_*.md` files explicitly call this
out (`# IMPORTANT: secret name is amjis-db-password, NOT amjis-app-db-password`).
No live infra was ever created under the `amjis-app-db-password` name —
treat any future reference to it as a typo and correct in place.

## §2 — The inconsistency

Two coexisting conventions:

1. **kebab-lower** (`amjis-db-password`, `openai-api-key`, `mcp-internal-token`)
   — earlier secrets, pre-multi-provider parity.
2. **UPPER_SNAKE_MATCHES_ENV_VAR** (`ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, …)
   — adopted during Chat V2 R11 v2 (Multi-Provider Parity), where the
   secret ID was made identical to the consuming env-var name to make
   the bootstrap line in `deploy.yml` a tautology
   (`ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest`).

Both styles work; the inconsistency is purely cosmetic. The
UPPER_SNAKE convention is arguably better because the
`--update-secrets` and `--set-secrets` line then carries no information
asymmetry — `<env-var>=<secret-id>:<version>` reads as a no-op rename.

## §3 — Remediation recommendation (not done in unit 0b.2)

**Defer to a dedicated operations wave.** Rename plan if/when chosen:

| Current ID            | Proposed ID            | Risk                         |
|-----------------------|------------------------|------------------------------|
| `amjis-db-password`   | `DB_PASSWORD`          | DB downtime if Cloud Run rev rolls before secret resolves |
| `openai-api-key`      | `OPENAI_API_KEY`       | LLM call failure window      |
| `mcp-internal-token`  | `MCP_INTERNAL_TOKEN`   | MCP sidecar 401 window       |

Procedure (when scheduled):
1. Create the new secret (copy current `:latest` value to new ID).
2. Bump `:latest` of the new ID; smoke-read the new ID from a
   throwaway revision.
3. Switch `deploy.yml` / `cloudbuild*.yaml` to the new ID.
4. Deploy + smoke; on success, schedule the old ID for deletion
   after a 7-day soak.

## §4 — What unit 0b.2 actually changed

- Added `secret_scan.sh` (this directory) + CI wire in `.github/workflows/ci.yml`.
- Removed one literal credential default from `platform/scripts/set-password.ts`
  (fallback `'amjis2024'` → required `process.env.NEW_USER_PASSWORD` with
  hard-fail if unset). No Secret Manager entry was created for this; the
  script is run ad-hoc by an operator who supplies the password via env or argv.
- **Real live credential removed from HEAD** in
  `platform/scripts/load_chart_facts_local.py` (see §5 below).
- This document, for future reference.

The Secret Manager IDs themselves were **not** renamed.

## §5 — Real-credential incident (HEAD-only remediation)

While running the scanner during unit 0b.2 implementation, a **real
literal DB password** was discovered in:

- `platform/scripts/load_chart_facts_local.py:76` (introduced commit `0bcc5415`,
  2026-05-25, "dar: [DAR-P4-S14] load enhanced chart_facts v1.2 to DB").
- Literal form: `--db-url` `argparse` default of
  `postgresql://amjis_app:<31-char-secret>@127.0.0.1:5433/amjis`.

The literal password is the value of GCP Secret Manager ID
`amjis-db-password` (verified by length + format consistency with prior
Auth Proxy bootstraps documented in `00_ARCHITECTURE/CHAT_V2_STAGING_INVESTIGATION.md`).

### §5.1 — What unit 0b.2 did

- Replaced the literal with `os.environ.get("DATABASE_URL", "")` and
  added a hard-fail check (`sys.exit(1)`) if both `--db-url` and
  `$DATABASE_URL` are empty. The literal no longer exists in HEAD.
- The literal is **NOT** included in this document, this commit's
  diff text, the commit message, or any other tracked file.

### §5.2 — Follow-up actions required (out of scope for unit 0b.2)

The credential **still lives in git history** at commit `0bcc5415`
on `main`. Two follow-ups are needed:

1. **Rotate `amjis-db-password` in GCP Secret Manager.** This is the
   safest mitigation. Cloud Run revisions that consume
   `DB_PASSWORD=amjis-db-password:latest` will pick up the new
   version on next deploy; live revisions need a no-op redeploy.
2. **History scrubbing (optional, expensive).** Tools like `git filter-repo`
   or BFG Repo-Cleaner can excise the literal from history, but this
   force-pushes `main` and rewrites every downstream branch. Defer
   unless §5.2.1 is also true (the leak reached a public mirror).
   Cross-check with `git log --all -p -- platform/scripts/load_chart_facts_local.py`
   before deciding.

### §5.3 — Why this was not declared "halt_queue" mid-unit

The brief's halt-class trigger is "service account JSON key in a tracked
file." A DB password is also serious but less catastrophic — it grants
network-bounded Postgres access via Cloud SQL Auth Proxy, not arbitrary
GCP-level identity. The credential is single-purpose, single-tenant,
and rotatable by changing one Secret Manager version. Unit 0b.2
proceeded to completion with the literal removed from HEAD and the
rotation flagged here. The operator (native) should rotate at next
maintenance window.

