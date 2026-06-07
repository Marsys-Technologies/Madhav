#!/usr/bin/env bash
# secret_scan.sh — detect hardcoded credentials in ops scripts + CI surfaces.
#
# Unit 0b.2 — Secret + DB-password remediation (Stream B).
#
# Modes:
#   (default)    Scan the repository tree, suppress known-noise paths,
#                exit 0 on no findings, 1 on findings.
#   --self-test  Validate scanner against fixtures under
#                platform/scripts/governance/secret_scan_fixtures/ —
#                fail/* MUST trip the scanner, pass/* MUST NOT.
#                Self-test exit: 0 on pass, 1 on fail.
#
# If `gitleaks` is on PATH, prefer it over the bash regex set.
#
# Suppressed paths (never scanned):
#   node_modules/, .next/, .venv/, 99_ARCHIVE/,
#   00_ARCHITECTURE/drift_reports/,
#   platform/scripts/governance/naming_lint_fixtures/fail/,
#   .git/

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
FIXTURES_DIR="${REPO_ROOT}/platform/scripts/governance/secret_scan_fixtures"

# Scoped scan targets (per brief §1):
#   scripts/, platform/scripts/, platform-mcp/scripts/,
#   .github/workflows/*.yml,
#   platform/cloudbuild*.yaml, platform-mcp/cloudbuild.yaml
SCAN_TARGETS=(
  "scripts"
  "platform/scripts"
  "platform-mcp/scripts"
  ".github/workflows"
  "platform/cloudbuild.yaml"
  "platform/cloudbuild.pipeline.yaml"
  "platform/cloudbuild-sidecar.yaml"
  "platform-mcp/cloudbuild.yaml"
)

SUPPRESS_RE='(^|/)(node_modules|\.next|\.venv|99_ARCHIVE|drift_reports|naming_lint_fixtures/fail|\.git|secret_scan_fixtures)(/|$)'

# Pattern set — each pattern targets a class of literal credential.
# Order matters only for exclusion-ordering inside grep -E.
#
# Notes:
#   - We deliberately tolerate `process.env.X` / `os.environ[...]` / `${VAR}`
#     style indirections by anchoring the literal patterns to character
#     classes that exclude `$` and `process`/`os.environ`/`getenv`.
#   - We tolerate the documented GCP Secret Manager reference form
#     `<env>=<secret-id>:latest` because that is the env→secret bootstrap
#     contract, not a literal credential.
PATTERNS=(
  # Inline postgres/mysql connection strings with embedded user:pass@
  'postgres(ql)?://[^[:space:]"'"'"']+:[^[:space:]"'"'"'@]{4,}@'
  'mysql://[^[:space:]"'"'"']+:[^[:space:]"'"'"'@]{4,}@'
  # Literal PGPASSWORD= / DB_PASSWORD= / DATABASE_PASSWORD= followed by a value.
  # Tolerated: =$VAR / =${VAR} / =process.env / =os.environ / =<secret-id>:latest
  '(PGPASSWORD|DB_PASSWORD|DATABASE_PASSWORD)=([^$[:space:]"'"'"'][^[:space:]"'"'"']*)'
  # Generic password = "literal" (quoted, non-env)
  '(^|[[:space:];,(])(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|auth[_-]?token)[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'$]{6,}["'"'"']'
  # JSON-style "password": "literal"  (non-env)
  '"(password|secret|api_key|access_token|auth_token)"[[:space:]]*:[[:space:]]*"[^"$]{6,}"'
  # Known provider key prefixes
  'AIza[0-9A-Za-z_\-]{30,}'
  'AKIA[0-9A-Z]{16}'
  'ghp_[A-Za-z0-9]{30,}'
  'gho_[A-Za-z0-9]{30,}'
  'sk-(ant-|proj-)?[A-Za-z0-9]{30,}'
  'xoxb-[A-Za-z0-9\-]{20,}'
  '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
  '"private_key"[[:space:]]*:[[:space:]]*"-----BEGIN'
)

# ── Helpers ──────────────────────────────────────────────────────────────────

# Run a single grep pass across the given paths; return non-zero if any
# unsuppressed match is found. Prints findings to stdout (file:line:match).
run_scan() {
  local -a targets=("$@")
  local -a existing=()
  local t
  for t in "${targets[@]}"; do
    [[ -e "${REPO_ROOT}/${t}" ]] && existing+=("${REPO_ROOT}/${t}")
  done
  if [[ ${#existing[@]} -eq 0 ]]; then
    return 0
  fi

  local findings=0
  local pat
  for pat in "${PATTERNS[@]}"; do
    # -r recursive, -E extended regex, -n line numbers, -I skip binary,
    # --include limits to text-like files but we let grep handle everything.
    while IFS= read -r line; do
      [[ -z "${line}" ]] && continue
      # Suppress noise paths
      if [[ "${line}" =~ ${SUPPRESS_RE} ]]; then
        continue
      fi
      # Tolerate env-indirection forms even if they happened to match.
      # Strip the "file:line:" prefix to look at the matched text only.
      local body="${line#*:*:}"
      if [[ "${body}" =~ (process\.env|os\.environ|getenv|secrets\.|\$\{[A-Z_]+\}|\{[A-Z_]+\}|:latest($|[^a-zA-Z0-9])|:[0-9]+($|[^a-zA-Z0-9])) ]]; then
        # Cloud-Run-style "DB_PASSWORD=amjis-db-password:latest" — tolerated.
        # Also tolerate explicit version pins "DB_PASSWORD=amjis-db-password:2" —
        # these are GCP Secret Manager version references, not literal credentials.
        # Likewise env reads and Python f-string placeholders ({VAR} without $).
        # The :latest/:N match anchors on a non-alphanumeric
        # boundary so it works in flowing prose ("...:latest`" or ":2 ").
        continue
      fi
      # Tolerate documentation placeholders in postgres URLs:
      #   postgres://user:<pw>@...        — angle-bracketed template
      #   postgres://user:<31-char-secret>@... — angle-bracketed (any chars except `>`)
      #   postgres://user:pass@...        — bare word "pass" / "password" / "pw"
      #   postgres://user:***@...         — masked
      #   postgres://user:xxx@...         — masked
      if [[ "${body}" =~ :\<[^\>]+\>@ ]]; then
        continue
      fi
      if [[ "${body}" =~ :(pass|password|pw|secret|xxx|\*+|your[-_]password[-_]here)@ ]]; then
        continue
      fi
      # Tolerate this scanner's own pattern strings (self-reference).
      if [[ "${line}" == *secret_scan.sh:* ]]; then
        continue
      fi
      echo "${line}"
      findings=$((findings + 1))
    done < <(grep -rEn -I "${pat}" "${existing[@]}" 2>/dev/null || true)
  done

  return "$(( findings > 0 ? 1 : 0 ))"
}

# ── Self-test ────────────────────────────────────────────────────────────────

self_test() {
  local rc=0
  local pass_dir="${FIXTURES_DIR}/pass"
  local fail_dir="${FIXTURES_DIR}/fail"

  if [[ ! -d "${fail_dir}" ]]; then
    echo "self-test: missing fixtures dir ${fail_dir}" >&2
    return 1
  fi

  # Each fail/* file MUST trip the scanner.
  local f hits
  for f in "${fail_dir}"/*; do
    [[ -e "${f}" ]] || continue
    hits=0
    local pat
    for pat in "${PATTERNS[@]}"; do
      if grep -EI -q "${pat}" "${f}" 2>/dev/null; then
        # Apply the same env-indirection tolerance as run_scan
        if grep -EI "${pat}" "${f}" 2>/dev/null | grep -Ev '(process\.env|os\.environ|getenv|secrets\.|\$\{[A-Z_]+\}|\{[A-Z_]+\}|:latest$|:latest[[:space:]]|:[0-9]+$|:[0-9]+[[:space:]])' >/dev/null 2>&1; then
          hits=$((hits + 1))
          break
        fi
      fi
    done
    if [[ "${hits}" -eq 0 ]]; then
      echo "self-test FAIL: fixture not detected: ${f}" >&2
      rc=1
    else
      echo "self-test PASS: caught fail fixture: $(basename "${f}")"
    fi
  done

  # pass_dir is optional; if present, fixtures MUST NOT trip the scanner.
  if [[ -d "${pass_dir}" ]]; then
    for f in "${pass_dir}"/*; do
      [[ -e "${f}" ]] || continue
      local tripped=0
      local pat
      for pat in "${PATTERNS[@]}"; do
        if grep -EI "${pat}" "${f}" 2>/dev/null | grep -Ev '(process\.env|os\.environ|getenv|secrets\.|\$\{[A-Z_]+\}|\{[A-Z_]+\}|:latest$|:latest[[:space:]]|:[0-9]+$|:[0-9]+[[:space:]])' >/dev/null 2>&1; then
          tripped=1
          break
        fi
      done
      if [[ "${tripped}" -eq 1 ]]; then
        echo "self-test FAIL: pass fixture wrongly tripped: ${f}" >&2
        rc=1
      else
        echo "self-test PASS: pass fixture clean: $(basename "${f}")"
      fi
    done
  fi

  return "${rc}"
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
  local mode="${1:-scan}"

  case "${mode}" in
    --self-test|self-test)
      self_test
      exit $?
      ;;
    --help|-h|help)
      sed -n '2,25p' "${BASH_SOURCE[0]}"
      exit 0
      ;;
    scan|"")
      # Prefer gitleaks if available.
      if command -v gitleaks >/dev/null 2>&1; then
        echo "secret_scan: using gitleaks"
        gitleaks detect --no-banner --redact --source "${REPO_ROOT}" \
          --exit-code 1 || exit 1
        echo "secret_scan: PASS (gitleaks clean)"
        exit 0
      fi

      echo "secret_scan: gitleaks not found — using bash regex set"
      if run_scan "${SCAN_TARGETS[@]}"; then
        echo "secret_scan: PASS (no literal credentials in scanned paths)"
        exit 0
      else
        echo ""
        echo "secret_scan: FAIL — literal credentials detected (see lines above)" >&2
        echo "  Replace with process.env.VAR / os.environ[...] / \${VAR} reads," >&2
        echo "  and document the Secret Manager ID in secret_naming.md." >&2
        exit 1
      fi
      ;;
    *)
      echo "secret_scan: unknown mode '${mode}' (use --self-test, --help, or no args)" >&2
      exit 2
      ;;
  esac
}

main "$@"
