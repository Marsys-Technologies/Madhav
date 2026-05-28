---
status: COMPLETE
unit: 0b.2
wave: 0b
title: Secret + DB-password remediation (security debt)
stream: B
worktree: ../MadhavStreamB
blockedBy: []
on_red: halt_queue   # a leaked secret is systemic — stop the whole queue
---

## Context (self-contained)
Audit + Gemini flagged hardcoded DB passwords in dev/ops scripts and inconsistent Secret Manager naming. With
zero-touch prod autonomy there is no human to catch a leaked credential, so this lands early and gates hard.

## Scope
- Grep `scripts/`, `platform/scripts/` for literal passwords / `PGPASSWORD=` / inline connection strings;
  replace with `process.env` / `os.environ` reads from Secret Manager-backed env.
- Normalize Secret Manager references to a single naming scheme; pin versions (no `:latest`) where the
  deploy pipeline allows.
- Add `platform/scripts/governance/secret_scan.sh` (detect-secrets / gitleaks style) and wire it into CI so
  any future literal secret fails the build.
- Do NOT rotate live secrets here (that is a separate, logged op); only remove literals + add the scanner.

## Acceptance criteria (all automated)
1. `platform/scripts/governance/secret_scan.sh` exits 0 on the repo (no literal secrets remain).
2. The scanner fails on a seeded fixture secret (proves it works).
3. No script's behavior changes other than sourcing creds from env (smoke: a representative script still runs
   in dry-run with env-provided creds).

## must_not_touch
`platform/src/**`, `platform-mcp/src/**` (application code).

## Commit cadence / rollback
Commits: (1) add secret_scan + CI wire, (2) replace literals with env reads. Rollback = revert; note any
secret already removed from a script stays removed (env read is the correct state).
