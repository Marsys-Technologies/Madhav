#!/usr/bin/env bash
# secret_scan.sh — repo-wide detection of literal credentials committed to the tree.
#
# Unit 0b.2 — Secret + DB-password remediation (Stream B).
# Scope inverted 2026-07-30 by SAMĀPTI DVĀRAPĀLA RULING 3 (see §SCOPE below).
#
# ─────────────────────────────────────────────────────────────────────────────
# §SCOPE — what is scanned, stated exactly (no implicit gaps)
# ─────────────────────────────────────────────────────────────────────────────
# This scanner enumerates EVERY file git would carry:
#
#     git ls-files --cached --others --exclude-standard
#
# i.e. tracked files PLUS untracked-but-not-ignored files. That is the set of
# bytes that can reach a commit. There is NO allowlist of scanned directories.
# Everything is in scope unless it appears in SUPPRESS_RE below, and every
# SUPPRESS_RE entry carries a stated reason.
#
# Prior to 2026-07-30 this script scanned an allowlist of 8 SCAN_TARGETS
# (scripts/, platform/scripts/, platform-mcp/scripts/, .github/workflows/,
# 4 cloudbuild files) while its own docstring claimed a repo-wide scan with
# suppression. That gap let a plaintext production DB credential sit in
# 9 tracked files under 00_ARCHITECTURE/ and platform/migrations/__tests__/
# for ~2 months without the gate ever going red. Incident SAMAPTI-SEC-001;
# DVA RULING 3 in 00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md.
#
# Modes:
#   (default)    Scan per §SCOPE. Exit 0 on no findings, 1 on findings.
#   --self-test  Validate the scanner against fixtures under
#                platform/scripts/governance/secret_scan_fixtures/ —
#                fail/* MUST trip the scanner, pass/* MUST NOT.
#                Self-test exit: 0 on pass, 1 on fail.
#   --list-files Print the file set the scanner would inspect (audit aid).
#
# `gitleaks`, if on PATH, runs IN ADDITION to the bash regex set — never
# instead of it. (Before 2026-07-30 it short-circuited the bash set entirely,
# so CI, which has no gitleaks, exercised a different code path than a
# developer's laptop, and the fixtures proved nothing about the path that ran.)
#
# ─────────────────────────────────────────────────────────────────────────────
# §SUPPRESS — every excluded path, with its reason
# ─────────────────────────────────────────────────────────────────────────────
#   node_modules/ .next/ .venv/ __pycache__/ .git/ dist/ out/ coverage/
#       Vendored or generated; never authored here. Already gitignored — listed
#       defensively so the non-git `find` fallback behaves identically.
#   package-lock.json pnpm-lock.yaml yarn.lock poetry.lock
#       Machine-generated dependency lockfiles: integrity hashes and base64
#       digests only, no human-authored credential can be introduced there,
#       and the digest noise is a false-positive generator.
#   platform/scripts/governance/secret_scan_fixtures/
#       THIS scanner's own fixtures. They contain deliberately synthetic
#       credentials. They are not unscanned — they are scanned by --self-test,
#       which asserts fail/* trips and pass/* does not.
#   platform/scripts/governance/naming_lint_fixtures/fail/
#       Deliberate-violation fixtures owned by naming_lint.py.
#   platform/scripts/governance/secret_scan.sh
#       This file. Its PATTERNS array necessarily matches its own patterns.
#   00_ARCHITECTURE/drift_reports/
#       Machine-generated drift output, regenerated on every governance run.
#
# 99_ARCHIVE/ is NOT suppressed (it was, before 2026-07-30). A credential in a
# cold archive is still a committed credential.
#
# ─────────────────────────────────────────────────────────────────────────────
# §TOLERANCE — what a match is forgiven for, and why
# ─────────────────────────────────────────────────────────────────────────────
# Tolerance is applied to the MATCHED SUBSTRING, never to the whole line.
#   1. Env / secret-store indirection: process.env, os.environ, getenv,
#      Deno.env, ${VAR}, $VAR, {{ secrets.X }}, {VAR}.
#   2. GCP Secret Manager bootstrap reference `ENV=<secret-id>:latest|:<n>`,
#      anchored to the END of the match.
#   3. Documentation placeholders: <angle-bracketed>, user:pass@, ***, xxxxxx,
#      REPLACE_ME, your-…, example.com, PLACEHOLDER.
#   4. "Weak placeholder" values: length <= 16 AND containing one of
#      test/fake/dummy/sample/xyz/changeme/placeholder/local/postgres/root/
#      admin/mysql/redacted/demo/example. The length bound is what keeps this
#      rule from forgiving a real 31/32/40-character credential that merely
#      contains "test". `fixture` is deliberately NOT a token — this scanner's
#      own fail/* fixtures must stay detectable.
#
# ─────────────────────────────────────────────────────────────────────────────
# §INHERITED — pre-existing findings, itemized and dated
# ─────────────────────────────────────────────────────────────────────────────
# Widening the scan surfaced findings that predate this gate. They are NOT
# silenced by re-narrowing scope. They are itemized one-per-line in
#     platform/scripts/governance/secret_scan_inherited.txt
# with an owner lane, an expiry date, and an expected occurrence count.
#   · A finding NOT in that register fails the build. Always.
#   · A registered finding whose count GREW fails the build.
#   · A registered finding past its expiry date fails the build.
#   · A registered finding that no longer matches is reported as RESOLVED and
#     the register line must be deleted (fatal under SECRET_SCAN_STRICT_REGISTER=1).
# The register can only shrink or expire. It cannot quietly absorb new leaks.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
FIXTURES_DIR="${REPO_ROOT}/platform/scripts/governance/secret_scan_fixtures"
INHERITED_FILE="${REPO_ROOT}/platform/scripts/governance/secret_scan_inherited.txt"
STRICT_REGISTER="${SECRET_SCAN_STRICT_REGISTER:-0}"
TODAY="$(date -u +%Y-%m-%d)"

SUPPRESS_RE='(^|/)(node_modules|\.next|\.venv|__pycache__|\.git|dist|out|coverage|drift_reports|secret_scan_fixtures)(/|$)|(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock)$|(^|/)naming_lint_fixtures/fail(/|$)|(^|/)secret_scan\.sh$'

# ─────────────────────────────────────────────────────────────────────────────
# Pattern set. PATTERN_IDS and PATTERNS are parallel arrays; the ID is the
# stable handle used by the inherited register (indices would churn on reorder).
# ─────────────────────────────────────────────────────────────────────────────
PATTERN_IDS=(
  pg_conn_string
  mysql_conn_string
  env_password_assign
  env_read_literal_default
  quoted_password_kv
  json_password_kv
  gcp_api_key
  aws_access_key
  github_pat
  github_oauth
  anthropic_openai_key
  slack_bot_token
  private_key_block
  json_private_key
)

PATTERNS=(
  # 1. Inline postgres/mysql connection strings with an embedded user:pass@.
  #    Catches the `.psql_url` shape:  postgresql://user:<literal>@host:5432/db
  'postgres(ql)?://[^[:space:]"'"'"']+:[^[:space:]"'"'"'@]{4,}@'
  # 2. Same for mysql.
  'mysql://[^[:space:]"'"'"']+:[^[:space:]"'"'"'@]{4,}@'
  # 3. A password-bearing env/shell variable assigned a literal.
  #    The value may be quoted — the pre-2026-07-30 pattern required the value's
  #    first character to be unquoted, so `PGPASSWORD="<literal>" psql ...` and
  #    `DB_PASS="<literal>"` both slipped through. Both are incident shapes.
  '(PGPASSWORD|PGPASS|PG_PASSWORD|DB_PASS|DB_PASSWORD|DATABASE_PASSWORD|POSTGRES_PASSWORD|MYSQL_PASSWORD|MYSQL_PWD|REDIS_PASSWORD|ADMIN_PASSWORD)[[:space:]]*=[[:space:]]*["'"'"']?[^$"'"'"'[:space:]][^"'"'"'[:space:]]{5,}'
  # 3b. An env READ whose FALLBACK DEFAULT is a literal credential:
  #        os.environ.get("DB_PASSWORD", "<literal>")
  #        os.getenv("DB_PASSWORD", "<literal>")
  #        process.env.DB_PASSWORD || "<literal>"      (also ??)
  #     This is the second, independent gap. `platform/scripts/` was ALREADY an
  #     old SCAN_TARGET, yet platform/scripts/governance/v13_production_gate.py:13
  #     carried a live credential in exactly this shape and was never flagged:
  #     the old patterns keyed on `DB_PASSWORD=`, and here the name sits inside a
  #     quoted argument. Note also that this pattern is deliberately EXEMPT from
  #     the env-indirection tolerance below — for this shape the presence of
  #     `os.environ` is the finding, not the exoneration.
  '(os\.environ\.get|os\.getenv|getenv)\([[:space:]]*["'"'"'][A-Za-z0-9_]*(PASS|PASSWORD|SECRET|TOKEN|API_KEY|APIKEY|ACCESS_KEY|PRIVATE_KEY|CREDENTIAL|DSN|DATABASE_URL)["'"'"'][[:space:]]*,[[:space:]]*["'"'"'][^"'"'"']{6,}["'"'"']|process\.env(\.|\[["'"'"'])[A-Za-z0-9_]*(PASS|PASSWORD|SECRET|TOKEN|API_KEY|APIKEY|ACCESS_KEY|PRIVATE_KEY|CREDENTIAL|DSN|DATABASE_URL)(["'"'"']\])?[[:space:]]*(\|\||\?\?)[[:space:]]*["'"'"'][^"'"'"']{6,}["'"'"']'
  # 4. Generic  password = "literal"  /  password: 'literal'  /  password='literal'
  #    Boundary is widened from the pre-2026-07-30 `[[:space:];,(]` to "any char
  #    that cannot continue an identifier AND is not a dash", so an inline kwarg
  #    in a connect() call is caught — psycopg2.connect(..., password='<lit>', ...)
  #    — while a gcloud CLI long-flag naming a Secret Manager ID is not
  #    (`--set-secrets ...,-secret="amjis-db-password"` is an ID, not a value).
  '(^|[^A-Za-z0-9_.-])(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|auth[_-]?token|client[_-]?secret)[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'$]{6,}["'"'"']'
  # 5. JSON-style "password": "literal"
  '"(password|secret|api_key|access_token|auth_token|client_secret)"[[:space:]]*:[[:space:]]*"[^"$]{6,}"'
  # 6-13. Known provider key prefixes / key material.
  'AIza[0-9A-Za-z_\-]{30,}'
  'AKIA[0-9A-Z]{16}'
  'ghp_[A-Za-z0-9]{30,}'
  'gho_[A-Za-z0-9]{30,}'
  'sk-(ant-|proj-)?[A-Za-z0-9]{30,}'
  'xoxb-[A-Za-z0-9\-]{20,}'
  '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
  '"private_key"[[:space:]]*:[[:space:]]*"-----BEGIN'
)

# ─────────────────────────────────────────────────────────────────────────────
# Tolerance
#
# Tolerance is evaluated against the MATCHED SUBSTRING, not the whole line.
# This is load-bearing. The pre-2026-07-30 scanner tolerated any line
# containing `:<digits>`, intended for Secret Manager version pins
# (`DB_PASSWORD=amjis-db-password:2`). Applied line-wide, that swallowed every
# connection string carrying a port — `postgresql://u:<literal>@host:5433/db`
# was tolerated because of the `:5433`. Match-scoped tolerance cannot do that:
# the match ends at the `@`, before the port.
# ─────────────────────────────────────────────────────────────────────────────

# Extract the credential VALUE out of a match, per pattern family.
#   pg_conn_string:  postgresql://user:VALUE@   → text between last ':' and '@'
#   everything else: KEY=VALUE / "key": "VALUE" → text after the last ':' or '='
# Surrounding quotes/backticks/spaces are stripped.
matched_value() {
  local m="$1" pid="$2" val
  case "$pid" in
    pg_conn_string|mysql_conn_string) val="${m%@*}"; val="${val##*:}" ;;
    # The default argument: the last quoted string in the match.
    env_read_literal_default)         val="${m%[\"\']}"; val="${val##*[\"\']}" ;;
    *)                                val="${m##*[:=]}" ;;
  esac
  val="${val//\"/}"; val="${val//\'/}"; val="${val//\`/}"; val="${val// /}"
  printf '%s' "${val}"
}

# A value is a "weak placeholder" when it is short AND reads as a throwaway.
# The length bound is load-bearing: it is what stops this rule from tolerating
# a real 31/32/40-character credential that merely happens to contain "test".
# Deliberately NOT in the token list: `fixture` — this scanner's own fail/*
# fixtures must stay detectable.
WEAK_MAX_LEN=16
WEAK_TOKENS='(test|fake|dummy|sample|xyz|changeme|placeholder|local|postgres|root|admin|mysql|redacted|demo|example)'

is_weak_placeholder() {
  local val="$1" lval
  [[ ${#val} -gt ${WEAK_MAX_LEN} ]] && return 1
  lval="$(printf '%s' "${val}" | tr 'A-Z' 'a-z')"
  [[ "${lval}" =~ ${WEAK_TOKENS} ]] && return 0
  return 1
}

is_tolerated() {
  local m="$1" pid="$2" val

  # Env / secret-store indirection, in any language we use.
  #
  # EXEMPTION: env_read_literal_default is precisely the shape where an env read
  # sits next to a hardcoded fallback credential. Forgiving it for containing
  # `os.environ` is how platform/scripts/governance/v13_production_gate.py:13
  # stayed invisible inside a directory the scanner was already reading.
  if [[ "$pid" != "env_read_literal_default" ]]; then
    if [[ "$m" =~ (process\.env|os\.environ|os\.getenv|getenv|Deno\.env|secrets\.|\$\{[A-Za-z_][A-Za-z0-9_]*|\$[A-Za-z_][A-Za-z0-9_]*|\{\{) ]]; then
      return 0
    fi
    # Python f-string / template placeholder: {VAR} with no literal payload.
    if [[ "$m" =~ \{[A-Za-z_][A-Za-z0-9_]*\} ]]; then
      return 0
    fi
  fi

  val="$(matched_value "$m" "$pid")"
  is_weak_placeholder "${val}" && return 0

  case "$pid" in
    env_read_literal_default)
      # A numeric default is a budget/port/timeout, not a credential.
      [[ "$val" =~ ^[0-9]+$ ]] && return 0
      # A URL-shaped default with no `user:pass@` userinfo carries no credential
      # (e.g. `process.env.DATABASE_URL ?? 'postgresql://app@localhost:5433/db'`).
      # If it DOES carry one, pg_conn_string / mysql_conn_string catch it
      # independently — this tolerance cannot hide a credential-bearing URL.
      if [[ "$val" =~ ^[a-zA-Z][a-zA-Z0-9+.-]*:// ]] && [[ ! "$val" =~ ://[^/@]*:[^/@]*@ ]]; then
        return 0
      fi
      ;;
    pg_conn_string|mysql_conn_string)
      # Documentation placeholders inside a connection string.
      #   postgres://user:<pw>@...          angle-bracketed template
      #   postgres://user:pass@...          bare word
      #   postgres://user:***@...           masked
      [[ "$m" =~ :\<[^\>]+\>@ ]] && return 0
      [[ "$m" =~ :(pass|passwd|password|pw|secret|xxx+|\*+|your[-_]password[-_]here)@ ]] && return 0
      ;;
    *)
      # GCP Secret Manager bootstrap reference: ENV=<secret-id>:latest | :<version>
      # Anchored to the END of the match (trailing markdown punctuation allowed)
      # so it cannot absorb a host:port the way the pre-2026-07-30 line-scoped
      # `:[0-9]+` tolerance did.
      [[ "$m" =~ =[A-Za-z0-9_.-]+:(latest|[0-9]+)[^A-Za-z0-9]*$ ]] && return 0
      # Obvious documentation placeholders.
      [[ "$m" =~ (REPLACE_ME|CHANGEME|xxxxxx|XXXXXX|\<[^\>]+\>|your[-_]|example\.com|PLACEHOLDER) ]] && return 0
      ;;
  esac
  return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# File enumeration
# ─────────────────────────────────────────────────────────────────────────────
# Provenance of the census: WHICH tree was measured.
#
# A census that cannot say what it measured is not a census (DVA RULING 30).
# This lane's own CRED-B count was queried on the suspicion that it had been
# taken against a stale tree; the register carried no SHA, so the only way to
# settle it was to re-derive the whole thing. Emitting the SHA makes that a
# one-line check next time.
scanned_provenance() {
  local sha state
  if git -C "${REPO_ROOT}" rev-parse --git-dir >/dev/null 2>&1; then
    sha="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo 'unknown')"
    if [[ -n "$(git -C "${REPO_ROOT}" status --porcelain 2>/dev/null)" ]]; then
      state="DIRTY (working tree differs from the commit above)"
    else
      state="clean"
    fi
    printf 'commit %s · worktree %s' "${sha}" "${state}"
  else
    printf 'not a git checkout (find fallback) · commit unknown'
  fi
}

enumerate_files() {
  if git -C "${REPO_ROOT}" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "${REPO_ROOT}" ls-files --cached --others --exclude-standard
  else
    # Non-git fallback (tarball checkout). Mirrors SUPPRESS_RE's directory set.
    ( cd "${REPO_ROOT}" && find . \
        \( -name node_modules -o -name .next -o -name .venv -o -name __pycache__ \
           -o -name .git -o -name dist -o -name out -o -name coverage \) -prune -o \
        -type f -print | sed 's|^\./||' )
  fi
}

scan_file_list() {
  local f
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    [[ "${f}" =~ ${SUPPRESS_RE} ]] && continue
    [[ -f "${REPO_ROOT}/${f}" ]] || continue
    printf '%s\n' "${f}"
  done < <(enumerate_files)
}

# Emit "pattern_id<TAB>path<TAB>lineno" for every un-tolerated match.
# Deliberately does NOT emit the matched text — this scanner's output lands in
# CI logs, and CI logs are not a place to reprint a live credential.
collect_findings() {
  local list_file="$1"
  local i pid pat line rel lno body m untol

  for i in "${!PATTERNS[@]}"; do
    pid="${PATTERN_IDS[$i]}"
    pat="${PATTERNS[$i]}"
    while IFS= read -r line; do
      [[ -z "${line}" ]] && continue
      rel="${line%%:*}"
      lno="${line#*:}"; lno="${lno%%:*}"
      body="${line#*:*:}"
      untol=0
      while IFS= read -r m; do
        [[ -z "${m}" ]] && continue
        if ! is_tolerated "${m}" "${pid}"; then untol=1; break; fi
      done < <(printf '%s\n' "${body}" | grep -oE "${pat}" 2>/dev/null || true)
      [[ "${untol}" -eq 1 ]] && printf '%s\t%s\t%s\n' "${pid}" "${rel}" "${lno}"
    done < <( cd "${REPO_ROOT}" && tr '\n' '\0' < "${list_file}" \
                | xargs -0 grep -HEnI --binary-files=without-match "${pat}" 2>/dev/null || true )
  done
}

# ─────────────────────────────────────────────────────────────────────────────
# Main scan
# ─────────────────────────────────────────────────────────────────────────────
run_scan() {
  local tmp; tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp}"' RETURN

  scan_file_list > "${tmp}/files"
  local nfiles; nfiles="$(wc -l < "${tmp}/files" | tr -d ' ')"
  echo "secret_scan: scanned tree — $(scanned_provenance)"
  echo "secret_scan: scanning ${nfiles} files (repo-wide minus SUPPRESS_RE; see script header §SCOPE)"

  # A scanner that scans nothing exits 0 and reads as green. That is the exact
  # failure class this lane exists to remove, so refuse to pass on an empty or
  # implausibly small surface rather than report a hollow success.
  if [[ "${nfiles}" -lt 100 ]]; then
    echo "secret_scan: FAIL - scan surface is ${nfiles} files, which cannot be right." >&2
    echo "  Expected the whole repository. Check that this is a git checkout with an" >&2
    echo "  index (git ls-files) or that the find fallback can read the tree." >&2
    return 1
  fi

  collect_findings "${tmp}/files" | sort -u > "${tmp}/findings"

  # Actual counts per (path, pattern_id).
  awk -F'\t' '{print $2"\t"$1}' "${tmp}/findings" | sort | uniq -c \
    | sed -E 's/^ *([0-9]+) /\1\t/' | awk -F'\t' '{print $2"\t"$3"\t"$1}' > "${tmp}/actual"

  local rc=0
  local -a new_findings=() grown=() expired=() resolved=() inherited_ok=()

  # Load register.
  : > "${tmp}/reg_keys"
  if [[ -f "${INHERITED_FILE}" ]]; then
    local rline rpath rpid rcount rowner rexp actual
    while IFS= read -r rline; do
      [[ -z "${rline}" || "${rline}" =~ ^[[:space:]]*# ]] && continue
      rpath="$(printf '%s' "${rline}" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/,"",$1); print $1}')"
      rpid="$(printf  '%s' "${rline}" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/,"",$2); print $2}')"
      rcount="$(printf '%s' "${rline}" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/,"",$3); print $3}')"
      rowner="$(printf '%s' "${rline}" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/,"",$4); print $4}')"
      rexp="$(printf  '%s' "${rline}" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/,"",$5); print $5}')"
      [[ -z "${rpath}" || -z "${rpid}" ]] && continue
      printf '%s\t%s\n' "${rpath}" "${rpid}" >> "${tmp}/reg_keys"

      actual="$(awk -F'\t' -v p="${rpath}" -v i="${rpid}" '$1==p && $2==i {print $3}' "${tmp}/actual")"
      actual="${actual:-0}"

      if [[ "${rexp}" < "${TODAY}" ]]; then
        expired+=("${rpath} [${rpid}] owner=${rowner} expired=${rexp}")
        rc=1
      elif [[ "${actual}" -gt "${rcount}" ]]; then
        grown+=("${rpath} [${rpid}] expected<=${rcount} actual=${actual} owner=${rowner}")
        rc=1
      elif [[ "${actual}" -eq 0 ]]; then
        resolved+=("${rpath} [${rpid}] owner=${rowner} — delete this register line")
        [[ "${STRICT_REGISTER}" == "1" ]] && rc=1
      else
        inherited_ok+=("${rpath} [${rpid}] ${actual}/${rcount} owner=${rowner} expires=${rexp}")
      fi
    done < "${INHERITED_FILE}"
  fi
  sort -u -o "${tmp}/reg_keys" "${tmp}/reg_keys" 2>/dev/null || true

  # Any finding whose (path, pattern_id) is not registered is NEW → fail.
  local fpath fpid fcount
  while IFS=$'\t' read -r fpath fpid fcount; do
    [[ -z "${fpath}" ]] && continue
    if ! grep -qxF "$(printf '%s\t%s' "${fpath}" "${fpid}")" "${tmp}/reg_keys" 2>/dev/null; then
      new_findings+=("${fpath} [${fpid}] x${fcount}")
      rc=1
    fi
  done < "${tmp}/actual"

  # ── Report ────────────────────────────────────────────────────────────────
  if [[ ${#inherited_ok[@]} -gt 0 ]]; then
    echo ""
    echo "secret_scan: INHERITED findings (registered, dated, NOT silenced):"
    printf '  - %s\n' "${inherited_ok[@]}"
  fi
  if [[ ${#resolved[@]} -gt 0 ]]; then
    echo ""
    echo "secret_scan: RESOLVED - register lines that no longer match:"
    printf '  - %s\n' "${resolved[@]}"
    echo "  (non-fatal; set SECRET_SCAN_STRICT_REGISTER=1 to make register rot fatal)"
  fi
  if [[ ${#expired[@]} -gt 0 ]]; then
    echo "" >&2
    echo "secret_scan: EXPIRED inherited findings - the deadline passed, remediate:" >&2
    printf '  - %s\n' "${expired[@]}" >&2
  fi
  if [[ ${#grown[@]} -gt 0 ]]; then
    echo "" >&2
    echo "secret_scan: GROWN inherited findings - a registered file gained new matches:" >&2
    printf '  - %s\n' "${grown[@]}" >&2
  fi
  if [[ ${#new_findings[@]} -gt 0 ]]; then
    echo "" >&2
    echo "secret_scan: NEW literal-credential findings (unregistered):" >&2
    printf '  - %s\n' "${new_findings[@]}" >&2
    echo "" >&2
    echo "  Matched text is deliberately not printed - run the pattern locally if you" >&2
    echo "  need it, and never paste a credential into a CI log or a commit message." >&2
    echo "  Fix: replace the literal with process.env.VAR / os.environ[...] / \${VAR}," >&2
    echo "  and document the Secret Manager ID in secret_naming.md." >&2
  fi

  return "${rc}"
}

# ─────────────────────────────────────────────────────────────────────────────
# Self-test — exercises the SAME collect/tolerate code path as run_scan.
# (Before 2026-07-30 the self-test re-implemented tolerance with a different,
#  line-scoped regex, so a green self-test proved nothing about the real scan.)
# ─────────────────────────────────────────────────────────────────────────────
file_trips_scanner() {
  local target="$1"
  local i pid pat body m
  for i in "${!PATTERNS[@]}"; do
    pid="${PATTERN_IDS[$i]}"
    pat="${PATTERNS[$i]}"
    while IFS= read -r body; do
      [[ -z "${body}" ]] && continue
      while IFS= read -r m; do
        [[ -z "${m}" ]] && continue
        is_tolerated "${m}" "${pid}" || { echo "${pid}"; return 0; }
      done < <(printf '%s\n' "${body}" | grep -oE "${pat}" 2>/dev/null || true)
    done < <(grep -EI --binary-files=without-match "${pat}" "${target}" 2>/dev/null || true)
  done
  return 1
}

self_test() {
  local rc=0
  local pass_dir="${FIXTURES_DIR}/pass"
  local fail_dir="${FIXTURES_DIR}/fail"

  if [[ ! -d "${fail_dir}" ]]; then
    echo "self-test: missing fixtures dir ${fail_dir}" >&2
    return 1
  fi

  local f hit
  for f in "${fail_dir}"/*; do
    [[ -f "${f}" ]] || continue
    if hit="$(file_trips_scanner "${f}")"; then
      echo "self-test PASS: caught fail fixture: $(basename "${f}")  [${hit}]"
    else
      echo "self-test FAIL: fixture not detected: ${f}" >&2
      rc=1
    fi
  done

  if [[ -d "${pass_dir}" ]]; then
    for f in "${pass_dir}"/*; do
      [[ -f "${f}" ]] || continue
      if hit="$(file_trips_scanner "${f}")"; then
        echo "self-test FAIL: pass fixture wrongly tripped: ${f}  [${hit}]" >&2
        rc=1
      else
        echo "self-test PASS: pass fixture clean: $(basename "${f}")"
      fi
    done
  fi

  # The scanner must not be able to pass by scanning nothing. Assert the real
  # scan surface reaches the directory trees the old allowlist missed and that
  # the SAMAPTI-SEC-001 leak actually lived in.
  #
  # NB: the list is materialised to a file rather than piped into `grep -q`.
  # Under `set -o pipefail`, `grep -q` exits on its first hit, the upstream
  # writer takes SIGPIPE, and the pipeline reports 141 — a true assertion would
  # read as a failure. (Caught while writing this; keep the temp file.)
  local surf; surf="$(mktemp)"
  scan_file_list > "${surf}"
  local d missing=0
  for d in "00_ARCHITECTURE/" "platform/migrations/" "platform/src/" "platform-mcp/src/" "infra/" "99_ARCHIVE/"; do
    if ! grep -q "^${d}" "${surf}"; then
      echo "self-test FAIL: scan surface does not reach ${d}" >&2
      missing=1
    fi
  done
  rm -f "${surf}"
  if [[ "${missing}" -eq 0 ]]; then
    echo "self-test PASS: scan surface reaches 00_ARCHITECTURE/, platform/migrations/, platform/src/, platform-mcp/src/, infra/, 99_ARCHIVE/"
  else
    rc=1
  fi

  return "${rc}"
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
main() {
  local mode="${1:-scan}"

  case "${mode}" in
    --self-test|self-test)
      self_test
      exit $?
      ;;
    --list-files|list-files)
      scan_file_list
      exit 0
      ;;
    --help|-h|help)
      # Print the whole header block, whatever its length (no hardcoded range —
      # a stale range is how a docstring drifts out of sync with the code).
      sed -n '2,/^set -uo pipefail/p' "${BASH_SOURCE[0]}" | sed '$d'
      exit 0
      ;;
    scan|"")
      local rc=0
      if run_scan; then
        echo ""
        echo "secret_scan: PASS (no new literal credentials) — $(scanned_provenance)"
      else
        rc=1
        echo "" >&2
        echo "secret_scan: FAIL - see findings above — $(scanned_provenance)" >&2
      fi

      # gitleaks runs IN ADDITION, never instead of, the bash set.
      if command -v gitleaks >/dev/null 2>&1; then
        echo ""
        echo "secret_scan: gitleaks present - running as an additional pass"
        if ! gitleaks detect --no-banner --redact --source "${REPO_ROOT}" --exit-code 1; then
          echo "secret_scan: FAIL - gitleaks reported findings" >&2
          rc=1
        else
          echo "secret_scan: gitleaks clean"
        fi
      fi
      exit "${rc}"
      ;;
    *)
      echo "secret_scan: unknown mode '${mode}' (use --self-test, --list-files, --help, or no args)" >&2
      exit 2
      ;;
  esac
}

main "$@"
