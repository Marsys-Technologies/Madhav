#!/usr/bin/env bash
# native_setup.sh — one script for the native to run once.
#
# Automates NATIVE_SETUP_v1_0.md (see NATIVE_SETUP_v1_1.md for the plain-English guide):
#   NS.1  create the swarm's macOS user + campaign group
#   NS.2  create the build broker account + its one sudoers rule (validated before install)
#   NS.3  lock the native's own credential-like files so the swarm account can never read them
#   NS.4  set folder ownership/ACLs for the campaign folders vs. the authority/config/control folders
#   NS.8  install the always-on LaunchDaemons, only if their plist files already exist
#   NS.9  power + software-update settings for the campaign
# Interactive helpers for the two steps that need a browser:
#   NS.5  --github-token   hand the swarm's GitHub bot token to the suvarna account
#   NS.7  --claude-token   hand a Claude Code long-lived token to the suvarna account
#
# Usage:  sudo bash native_setup.sh [--check|--apply|--undo|--verify|--github-token|--claude-token]
#   --check   (default when not root) — read-only. Prints what is already done and what would be
#             done. Changes nothing. Exit 0.
#   --apply   (root only) — idempotent. Every step checks its own state first; a step already done
#             prints "already done" and changes nothing.
#   --undo    (root only) — reverses what --apply created: the 'suvarna' and '_suvarnabuild' users,
#             the 'suvarna-campaign' group, the sudoers file, the LaunchDaemons, and folder
#             ownership (back to the invoking user). Never deletes a data folder — only ownership/ACL.
#   --verify  (root only) — runs every post-check from the setup document and writes a flat
#             PASS/FAIL JSON map to $SUVARNA_HOME/evidence/launch/NS_VERIFY.json.
#   --github-token / --claude-token — interactive helpers for NS.5 / NS.7 (see above).
#
# On any failure, --apply stops immediately, explains in plain English what failed, and prints the
# exact --undo command. Nothing after the failed step is touched.
#
# Testing: set NATIVE_SETUP_SIMULATE=1 (with NATIVE_SETUP_SIM_LOG and NATIVE_SETUP_SIM_STATE also
# set) to run this whole script against a fake in-memory system: every command that would mutate or
# query real macOS state is replaced by a small logger/state-file pair, so nothing real is ever
# touched. See suvarna_tracker/tests/test_native_setup.py.
set -euo pipefail

SCRIPT_VERSION="1.0"
SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"

# ---------------------------------------------------------------------------------------------
# Configuration (documented paths only — nothing outside this list is ever touched)
# ---------------------------------------------------------------------------------------------
SUVARNA_HOME="${SUVARNA_HOME:-/Users/Dev/suvarna}"
NATIVE_SETUP_HOME_ROOT="${NATIVE_SETUP_HOME_ROOT:-/Users/Dev}"     # NS.3 credential scan root
CONTROL_ROOT="${NATIVE_SETUP_CONTROL_ROOT:-$SUVARNA_HOME/control}"  # NS.2 / NS.8 source of truth
PYTHON_BIN="${NATIVE_SETUP_PYTHON_BIN:-/opt/homebrew/bin/python3}"
BROKER_SCRIPT="$CONTROL_ROOT/platform/scripts/governance/suvarna_tracker/broker.py"
SUDOERS_FILE="/etc/sudoers.d/suvarna-build"
SUDOERS_LINE="suvarna ALL=(_suvarnabuild) NOPASSWD: $PYTHON_BIN $BROKER_SCRIPT *"
LAUNCHD_DIR="/Library/LaunchDaemons"
LAUNCHD_SRC_DIR="$CONTROL_ROOT/platform/scripts/governance/suvarna_tracker/runtime/launchd"
NS8_SERVICES="tracker monitor runner.engine runner.exec"
KEYCHAIN_ITEM="suvarna-swarm-user"
VERIFY_OUT="$SUVARNA_HOME/evidence/launch/NS_VERIFY.json"

# ---------------------------------------------------------------------------------------------
# Simulation harness. Every command that would touch real macOS state goes through do_or_sim()
# below; every state *check* goes through a p_* predicate that branches the same way. Nothing
# under NATIVE_SETUP_SIMULATE=1 ever calls sysadminctl, dscl, dseditgroup, chown, chmod, chflags,
# launchctl, pmset, defaults, visudo, security, install, or tee to /etc.
# ---------------------------------------------------------------------------------------------
SIMULATE="${NATIVE_SETUP_SIMULATE:-0}"
SIM_LOG="${NATIVE_SETUP_SIM_LOG:-}"
SIM_STATE="${NATIVE_SETUP_SIM_STATE:-}"
SIM_ROOT="${NATIVE_SETUP_SIM_ROOT:-0}"
SIM_FAIL_AT="${NATIVE_SETUP_SIM_FAIL_AT:-}"

if [ "$SIMULATE" = "1" ]; then
  if [ -z "$SIM_LOG" ] || [ -z "$SIM_STATE" ]; then
    echo "NATIVE_SETUP_SIMULATE=1 requires NATIVE_SETUP_SIM_LOG and NATIVE_SETUP_SIM_STATE." >&2
    exit 2
  fi
  touch "$SIM_LOG" "$SIM_STATE"
fi

say() { printf '%s\n' "$*"; }

sim_state_get() {
  # Always exits 0 — "no such key" is a normal outcome under pipefail, not an error.
  { grep -m1 "^${1}=" "$SIM_STATE" 2>/dev/null || true; } | cut -d= -f2-
}

sim_state_set() {
  local key="$1" val="$2" tmp
  tmp="${SIM_STATE}.tmp.$$"
  { grep -v "^${key}=" "$SIM_STATE" 2>/dev/null || true; } > "$tmp"
  printf '%s=%s\n' "$key" "$val" >> "$tmp"
  mv "$tmp" "$SIM_STATE"
}

sim_state_is_true() {
  [ "$(sim_state_get "$1")" = "1" ]
}

# do_or_sim <state-keyspec|""> <step-id> <plain description, must never contain a secret> -- <real argv...>
#   state-keyspec: "key" (set to 1 on success) or "key=value" (set to value on success), or "" for none.
#   step-id: compared against NATIVE_SETUP_SIM_FAIL_AT to let tests inject a failure at this exact step.
do_or_sim() {
  local keyspec="$1" step="$2" desc="$3"
  shift 3
  if [ "${1:-}" = "--" ]; then shift; fi
  local key val
  case "$keyspec" in
    *=*) key="${keyspec%%=*}"; val="${keyspec#*=}" ;;
    "") key=""; val="" ;;
    *) key="$keyspec"; val="1" ;;
  esac
  if [ "$SIMULATE" = "1" ]; then
    if [ -n "$SIM_FAIL_AT" ] && [ "$SIM_FAIL_AT" = "$step" ]; then
      printf '[SIMULATED FAILURE at %s] %s\n' "$step" "$desc" >> "$SIM_LOG"
      return 1
    fi
    printf '%s\n' "$desc" >> "$SIM_LOG"
    [ -n "$key" ] && sim_state_set "$key" "$val"
    return 0
  fi
  "$@"
}

fail_step() {
  local step="$1" reason="$2"
  {
    printf '\nSTOPPED at %s: %s\n' "$step" "$reason"
    printf 'Nothing after this point was changed.\n'
    printf 'To undo everything this script has set up so far, run:\n'
    printf '  sudo bash %s --undo\n' "$SCRIPT_PATH"
  } >&2
  exit 1
}

# ---------------------------------------------------------------------------------------------
# Generic state predicates (real branch is read-only and needs no privilege; safe under --check)
# ---------------------------------------------------------------------------------------------
p_user_exists() {  # $1 = username
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "user_${1}_exists"
  else id "$1" >/dev/null 2>&1
  fi
}

p_group_exists() {  # $1 = groupname
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "group_${1}_exists"
  else dscl . -read "/Groups/$1" >/dev/null 2>&1
  fi
}

p_user_in_group() {  # $1 = user, $2 = group
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "member_${2}_${1}"
  else dseditgroup -o checkmember -m "$1" "$2" >/dev/null 2>&1
  fi
}

is_running_as_root() {
  if [ "$SIMULATE" = "1" ]; then [ "$SIM_ROOT" = "1" ]
  else [ "$(id -u)" = "0" ]
  fi
}

# ---------------------------------------------------------------------------------------------
# NS.1 — swarm user + campaign group
# ---------------------------------------------------------------------------------------------
gen_password() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 33 | tr -dc 'A-Za-z0-9' | cut -c1-28
  else
    head -c 64 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | cut -c1-28
  fi
}

store_keychain_password() {  # $1 = keychain item name, $2 = password (never printed)
  if [ "$SIMULATE" = "1" ]; then
    printf 'security add-generic-password -a suvarna -s %s -w <redacted, generated password> -U /Library/Keychains/System.keychain\n' "$1" >> "$SIM_LOG"
    sim_state_set "ns1_keychain_stored" 1
    return 0
  fi
  security add-generic-password -a suvarna -s "$1" -w "$2" -U /Library/Keychains/System.keychain
}

ns1_check() {
  if p_user_exists suvarna && p_group_exists suvarna-campaign \
     && p_user_in_group Dev suvarna-campaign && p_user_in_group suvarna suvarna-campaign; then
    say "[done]    NS.1 — the swarm's macOS account and campaign group already exist."
  else
    say "[pending] NS.1 — would create the 'suvarna' account and 'suvarna-campaign' group."
  fi
}

ns1_apply() {
  say "Creating the separate account the agents will run as..."
  if p_user_exists suvarna; then
    say "  Already done — the 'suvarna' user exists."
  else
    local pass
    pass="$(gen_password)"
    if [ "$SIMULATE" = "1" ]; then
      if [ -n "$SIM_FAIL_AT" ] && [ "$SIM_FAIL_AT" = "NS.1" ]; then
        printf '[SIMULATED FAILURE at NS.1] create user suvarna\n' >> "$SIM_LOG"
        unset pass
        fail_step "NS.1" "could not create the 'suvarna' user."
      fi
      printf 'sysadminctl -addUser suvarna -fullName "Suvarna swarm" -shell /bin/zsh -home /Users/suvarna -password <redacted, piped via stdin>\n' >> "$SIM_LOG"
      printf 'createhomedir -c -u suvarna\n' >> "$SIM_LOG"
      printf 'dscl . create /Users/suvarna IsHidden 1\n' >> "$SIM_LOG"
      sim_state_set "user_suvarna_exists" 1
    else
      printf '%s' "$pass" | sysadminctl -addUser suvarna -fullName "Suvarna swarm" -shell /bin/zsh -home /Users/suvarna -password - \
        || { unset pass; fail_step "NS.1" "could not create the 'suvarna' user (sysadminctl failed)."; }
      createhomedir -c -u suvarna || { unset pass; fail_step "NS.1" "could not create suvarna's home directory."; }
      dscl . create /Users/suvarna IsHidden 1 || { unset pass; fail_step "NS.1" "could not hide the 'suvarna' account from the login window."; }
    fi
    store_keychain_password "$KEYCHAIN_ITEM" "$pass" \
      || { unset pass; fail_step "NS.1" "created the user but could not save its password to the Keychain."; }
    unset pass
    say "  Done — 'suvarna' is a standard (non-admin) account; its password is in the System keychain, never shown."
  fi

  say "Creating the campaign group and adding the right accounts to it..."
  if ! p_group_exists suvarna-campaign; then
    do_or_sim "group_suvarna-campaign_exists" "NS.1" 'dseditgroup -o create -r "Suvarna campaign" suvarna-campaign' \
      -- dseditgroup -o create -r "Suvarna campaign" suvarna-campaign \
      || fail_step "NS.1" "could not create the 'suvarna-campaign' group."
  fi
  if ! p_user_in_group Dev suvarna-campaign; then
    do_or_sim "member_suvarna-campaign_Dev" "NS.1" "dseditgroup -o edit -a Dev -t user suvarna-campaign" \
      -- dseditgroup -o edit -a Dev -t user suvarna-campaign \
      || fail_step "NS.1" "could not add 'Dev' to the campaign group."
  fi
  if ! p_user_in_group suvarna suvarna-campaign; then
    do_or_sim "member_suvarna-campaign_suvarna" "NS.1" "dseditgroup -o edit -a suvarna -t user suvarna-campaign" \
      -- dseditgroup -o edit -a suvarna -t user suvarna-campaign \
      || fail_step "NS.1" "could not add 'suvarna' to the campaign group."
  fi
  say "  Done — 'suvarna-campaign' group holds both 'suvarna' and 'Dev'; 'suvarna' is not an administrator."
}

ns1_verify() {
  if p_user_exists suvarna; then add_verify "ns1_user_created" PASS; else add_verify "ns1_user_created" FAIL; fi
  if p_user_in_group Dev suvarna-campaign; then add_verify "ns1_dev_in_campaign_group" PASS; else add_verify "ns1_dev_in_campaign_group" FAIL; fi
  if p_user_in_group suvarna suvarna-campaign; then add_verify "ns1_suvarna_in_campaign_group" PASS; else add_verify "ns1_suvarna_in_campaign_group" FAIL; fi
  if p_user_in_group suvarna admin; then add_verify "ns1_suvarna_not_admin" FAIL; else add_verify "ns1_suvarna_not_admin" PASS; fi
}

ns1_undo() {
  if p_user_exists suvarna; then
    do_or_sim "user_suvarna_exists=0" "UNDO" "sysadminctl -deleteUser suvarna" -- sysadminctl -deleteUser suvarna \
      || { say "  Could not delete the 'suvarna' user."; return 1; }
    do_or_sim "ns1_keychain_stored=0" "UNDO" "security delete-generic-password -s $KEYCHAIN_ITEM" \
      -- security delete-generic-password -s "$KEYCHAIN_ITEM" || true
  fi
  if p_group_exists suvarna-campaign; then
    do_or_sim "group_suvarna-campaign_exists=0" "UNDO" "dseditgroup -o delete suvarna-campaign" -- dseditgroup -o delete suvarna-campaign \
      || { say "  Could not delete the 'suvarna-campaign' group."; return 1; }
  fi
  return 0
}

# ---------------------------------------------------------------------------------------------
# NS.2 — build broker account + one sudoers rule
# ---------------------------------------------------------------------------------------------
p_broker_user_exists() { p_user_exists "_suvarnabuild"; }

p_broker_dir_ready() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns2_broker_dir_ready"
  else
    [ -d "$SUVARNA_HOME/broker" ] \
      && [ "$(stat -f '%Su' "$SUVARNA_HOME/broker" 2>/dev/null)" = "_suvarnabuild" ] \
      && [ "$(stat -f '%Lp' "$SUVARNA_HOME/broker" 2>/dev/null)" = "700" ]
  fi
}

p_sudoers_installed() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns2_sudoers_installed"
  else [ -f "$SUDOERS_FILE" ] && grep -qF "$SUDOERS_LINE" "$SUDOERS_FILE" 2>/dev/null
  fi
}

choose_broker_uid() {
  local used uid
  if [ "$SIMULATE" = "1" ]; then
    used=",$(sim_state_get "ns2_used_uids"),"
  else
    used=",$(dscl . -list /Users UniqueID 2>/dev/null | awk '{print $2}' | tr '\n' ',' || true),"
  fi
  for uid in $(seq 300 399); do
    case "$used" in
      *",$uid,"*) continue ;;
      *) printf '%s' "$uid"; return 0 ;;
    esac
  done
  return 1
}

ns2_check() {
  if p_broker_user_exists && p_broker_dir_ready && p_sudoers_installed; then
    say "[done]    NS.2 — the build broker account and its sudo rule already exist."
  else
    say "[pending] NS.2 — would create '_suvarnabuild' and its one validated sudoers rule."
  fi
}

ns2_apply() {
  say "Setting up the build broker account and its one sudo rule..."
  if p_broker_user_exists; then
    say "  Already done — the '_suvarnabuild' account exists."
  else
    local uid
    uid="$(choose_broker_uid)" || fail_step "NS.2" "no free user id in 300-399 for the build broker."
    do_or_sim "user__suvarnabuild_exists" "NS.2" "sysadminctl -addUser _suvarnabuild -fullName 'Suvarna build broker' -UID $uid -roleAccount -shell /usr/bin/false" \
      -- sysadminctl -addUser _suvarnabuild -fullName "Suvarna build broker" -UID "$uid" -roleAccount -shell /usr/bin/false \
      || fail_step "NS.2" "could not create the '_suvarnabuild' role account."
    say "  Done — created '_suvarnabuild' (uid $uid); the builder credential will belong only to it."
  fi

  if ! p_broker_dir_ready; then
    do_or_sim "ns2_broker_dir_ready" "NS.2" "mkdir -p $SUVARNA_HOME/broker; chown _suvarnabuild it; chmod 700 it" \
      -- ns2_make_broker_dir \
      || fail_step "NS.2" "could not lock down the broker's folder."
  fi

  if p_sudoers_installed; then
    say "  Already done — the sudo rule is installed."
  else
    say "Writing the one sudo rule the swarm may use (checked for syntax errors before it is installed)..."
    local tmpf
    tmpf="$(mktemp /tmp/suvarna-sudoers.XXXXXX)"
    printf '%s\n' "$SUDOERS_LINE" > "$tmpf"
    if [ "$SIMULATE" = "1" ]; then
      if [ -n "$SIM_FAIL_AT" ] && [ "$SIM_FAIL_AT" = "NS.2-validate" ]; then
        printf '[SIMULATED FAILURE at NS.2-validate] visudo -cf %s\n' "$tmpf" >> "$SIM_LOG"
        rm -f "$tmpf"
        fail_step "NS.2" "the generated sudoers rule failed the syntax check (visudo); nothing was installed."
      fi
      printf 'visudo -cf <tempfile> -> parsed OK\n' >> "$SIM_LOG"
    else
      if ! visudo -cf "$tmpf" >/dev/null 2>&1; then
        rm -f "$tmpf"
        fail_step "NS.2" "the generated sudoers rule failed the syntax check (visudo); nothing was installed."
      fi
    fi
    do_or_sim "ns2_sudoers_installed" "NS.2" "install the checked sudoers rule to $SUDOERS_FILE (mode 440, root:wheel)" \
      -- sh -c "install -o root -g wheel -m 440 '$tmpf' '$SUDOERS_FILE'" \
      || { rm -f "$tmpf"; fail_step "NS.2" "could not install the sudoers rule."; }
    rm -f "$tmpf"
    say "  Done — the swarm may run exactly one program with elevated rights: the build broker."
  fi
}

ns2_make_broker_dir() {
  mkdir -p "$SUVARNA_HOME/broker"
  chown _suvarnabuild "$SUVARNA_HOME/broker"
  chmod 700 "$SUVARNA_HOME/broker"
}

ns2_verify() {
  if p_broker_user_exists; then add_verify "ns2_broker_created" PASS; else add_verify "ns2_broker_created" FAIL; fi
  if p_broker_dir_ready; then add_verify "ns2_broker_folder_locked" PASS; else add_verify "ns2_broker_folder_locked" FAIL; fi
  if p_sudoers_installed; then add_verify "ns2_sudo_rule_installed" PASS; else add_verify "ns2_sudo_rule_installed" FAIL; fi
}

ns2_undo() {
  local rc=0
  if p_sudoers_installed; then
    do_or_sim "ns2_sudoers_installed=0" "UNDO" "rm -f $SUDOERS_FILE" -- rm -f "$SUDOERS_FILE" \
      || { say "  Could not remove the sudoers file."; rc=1; }
  fi
  if p_broker_user_exists; then
    do_or_sim "user__suvarnabuild_exists=0" "UNDO" "sysadminctl -deleteUser _suvarnabuild" -- sysadminctl -deleteUser _suvarnabuild \
      || { say "  Could not delete the '_suvarnabuild' account."; rc=1; }
  fi
  if [ -d "$SUVARNA_HOME/broker" ]; then
    do_or_sim "ns2_broker_dir_ready=0" "UNDO" "chown \${SUDO_USER:-Dev}:staff $SUVARNA_HOME/broker (ownership only)" \
      -- ns2_undo_broker_dir_owner || { say "  Could not restore ownership of the broker folder."; rc=1; }
  fi
  return $rc
}

ns2_undo_broker_dir_owner() {
  chown "${SUDO_USER:-Dev}:staff" "$SUVARNA_HOME/broker"
}

# ---------------------------------------------------------------------------------------------
# NS.3 — lock the native's own credential-like files (read-only scan; chmod is idempotent by nature)
# ---------------------------------------------------------------------------------------------
NS3_OWN_DIRS="$HOME/.config/gh $HOME/.config/madhav-admin $HOME/.claude"

p_ns3_own_dirs_locked() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns3_own_dirs_locked"
  else
    local d
    for d in $NS3_OWN_DIRS; do
      [ -d "$d" ] || continue
      [ "$(stat -f '%Lp' "$d" 2>/dev/null)" = "700" ] || return 1
    done
    return 0
  fi
}

ns3_chmod_own_dirs() {
  local d
  for d in $NS3_OWN_DIRS; do
    [ -d "$d" ] || continue
    chmod 700 "$d"
  done
}

ns3_find_readable_secrets() {
  if [ "$SIMULATE" = "1" ]; then
    sim_state_get "ns3_pending_files" | tr ',' '\n' | { sed '/^$/d' || true; }
    return 0
  fi
  # Prune (never descend into) folders that cannot matter, so the scan takes seconds, not minutes.
  # ~/Library is pruned only when it is already private (mode 700: nobody else can traverse it).
  local lib_prune=()
  if [ -d "$NATIVE_SETUP_HOME_ROOT/Library" ] && [ "$(stat -f '%Lp' "$NATIVE_SETUP_HOME_ROOT/Library" 2>/dev/null)" = "700" ]; then
    lib_prune=(-o -path "$NATIVE_SETUP_HOME_ROOT/Library")
  fi
  find "$NATIVE_SETUP_HOME_ROOT" -maxdepth 8 \
    \( -name node_modules -o -name .git -o -name .venv -o -name venv -o -name __pycache__ -o -name .Trash \
       -o -name .next -o -name dist -o -name .cache "${lib_prune[@]}" \) -prune -o \
    \( -name '.env' -o -name '.env.*' -o -name 'dbenv*.sh' -o -name 'pgenv*.sh' -o -name '*key*.pem' \
       -o -name 'auth.json' -o -name 'hosts.yml' -o -name 'credentials*.json' -o -name '*service-account*.json' \) \
    ! -name '*.example' ! -name '*.sample' ! -name '*.template' ! -name '*.example.*' \
    -type f -perm -o=r -print 2>/dev/null || true
}

sim_ns3_mark_locked() {
  local f="$1" remaining
  remaining="$(sim_state_get "ns3_pending_files" | tr ',' '\n' | { sed '/^$/d' || true; } | { grep -vFx "$f" || true; } | { paste -sd, - || true; })"
  sim_state_set "ns3_pending_files" "$remaining"
}

ns3_check() {
  local pending
  say "          (scanning your home folder for credential files other accounts could read; up to a minute)"
  pending="$(ns3_find_readable_secrets)"
  if p_ns3_own_dirs_locked && [ -z "$pending" ]; then
    say "[done]    NS.3 — no credential-like file under $NATIVE_SETUP_HOME_ROOT is readable by anyone else."
  else
    say "[pending] NS.3 — would lock your own config folders and any readable credential-like files."
  fi
}

ns3_apply() {
  say "Locking your own credential-like files so the swarm account can never read them..."
  if ! p_ns3_own_dirs_locked; then
    do_or_sim "ns3_own_dirs_locked" "NS.3" "chmod 700 ~/.config/gh ~/.config/madhav-admin ~/.claude (existing ones only)" \
      -- ns3_chmod_own_dirs \
      || fail_step "NS.3" "could not lock your own config folders."
  fi

  local n=0 f
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    n=$((n + 1))
    if [ "$SIMULATE" = "1" ]; then
      if [ -n "$SIM_FAIL_AT" ] && [ "$SIM_FAIL_AT" = "NS.3" ]; then
        printf '[SIMULATED FAILURE at NS.3] chmod go-rwx %s\n' "$f" >> "$SIM_LOG"
        fail_step "NS.3" "could not lock $f."
      fi
      printf 'chmod go-rwx %s\n' "$f" >> "$SIM_LOG"
      sim_ns3_mark_locked "$f"
    else
      chmod go-rwx "$f" || fail_step "NS.3" "could not lock $f."
      say "  Locked: $f"
    fi
  done <<EOF
$(ns3_find_readable_secrets)
EOF
  if [ "$n" -eq 0 ]; then
    say "  Already done — no credential-like files were readable by anyone else."
  else
    say "  Done — locked $n file(s). Contents were never read or printed, only permissions changed."
  fi
}

ns3_verify() {
  local pending
  pending="$(ns3_find_readable_secrets)"
  if [ -z "$pending" ]; then add_verify "ns3_no_readable_secrets" PASS; else add_verify "ns3_no_readable_secrets" FAIL; fi
  if p_ns3_own_dirs_locked; then add_verify "ns3_own_dirs_locked" PASS; else add_verify "ns3_own_dirs_locked" FAIL; fi
}
# NS.3 is a one-way tightening of permissions. --undo intentionally does not loosen it back —
# re-exposing a credential file is never a safe "undo".

# ---------------------------------------------------------------------------------------------
# NS.4 — campaign folder ownership / ACLs
# ---------------------------------------------------------------------------------------------
NS4_SWARM_DIRS="hq trunk lanes evidence run .repo"
NS4_NATIVE_DIRS="authority config control"

p_ns4_folders_ready() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns4_folders_ready"
  else
    local d
    for d in $NS4_SWARM_DIRS; do
      [ -d "$SUVARNA_HOME/$d" ] || return 1
      [ "$(stat -f '%Su:%Sg' "$SUVARNA_HOME/$d" 2>/dev/null)" = "suvarna:suvarna-campaign" ] || return 1
    done
    for d in $NS4_NATIVE_DIRS; do
      [ -d "$SUVARNA_HOME/$d" ] || return 1
      [ "$(stat -f '%Su:%Sg' "$SUVARNA_HOME/$d" 2>/dev/null)" = "Dev:staff" ] || return 1
    done
    return 0
  fi
}

p_ns4_decisions_moved() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns4_decisions_moved"
  else
    [ ! -f "$SUVARNA_HOME/run/DECISIONS.jsonl" ] && [ ! -f "$SUVARNA_HOME/run/DECISIONS.jsonl.lock" ]
  fi
}

p_ns4_holds_ready() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns4_holds_ready"
  else
    [ -f "$SUVARNA_HOME/authority/HOLDS.jsonl" ] && [ -f "$SUVARNA_HOME/authority/HOLD_CLEARS.jsonl" ] \
      && [ "$(stat -f '%Su:%Sg' "$SUVARNA_HOME/authority/HOLDS.jsonl" 2>/dev/null)" = "Dev:suvarna-campaign" ]
  fi
}

p_ns4_pgenv_ready() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns4_pgenv_ready"
  else
    [ -f "/Users/suvarna/.config/suvarna/pgenv.sh" ] \
      && [ "$(stat -f '%Su' "/Users/suvarna/.config/suvarna/pgenv.sh" 2>/dev/null)" = "suvarna" ] \
      && [ "$(stat -f '%Lp' "/Users/suvarna/.config/suvarna/pgenv.sh" 2>/dev/null)" = "600" ]
  fi
}

ns4_check() {
  if p_ns4_folders_ready && p_ns4_decisions_moved && p_ns4_holds_ready && p_ns4_pgenv_ready; then
    say "[done]    NS.4 — campaign folder ownership is already set."
  else
    say "[pending] NS.4 — would set folder owners/ACLs and move the decisions log if still in place."
  fi
}

ns4_do_folders() {
  mkdir -p "$SUVARNA_HOME/hq" "$SUVARNA_HOME/trunk" "$SUVARNA_HOME/lanes" "$SUVARNA_HOME/evidence" \
    "$SUVARNA_HOME/run" "$SUVARNA_HOME/.repo" "$SUVARNA_HOME/authority" "$SUVARNA_HOME/config" "$SUVARNA_HOME/control"
  local d
  for d in $NS4_SWARM_DIRS; do
    chown -R suvarna:suvarna-campaign "$SUVARNA_HOME/$d"
    chmod 2775 "$SUVARNA_HOME/$d"
    chmod -R +a "group:suvarna-campaign allow list,search,add_file,add_subdirectory,delete_child,read,write,append,execute,readattr,writeattr,readextattr,writeextattr,readsecurity,file_inherit,directory_inherit" \
      "$SUVARNA_HOME/$d"
  done
  for d in $NS4_NATIVE_DIRS; do
    chown -R Dev:staff "$SUVARNA_HOME/$d"
    chmod 755 "$SUVARNA_HOME/$d"
  done
}

ns4_do_move_decisions() {
  [ -f "$SUVARNA_HOME/run/DECISIONS.jsonl" ] && mv "$SUVARNA_HOME/run/DECISIONS.jsonl" "$SUVARNA_HOME/authority/"
  [ -f "$SUVARNA_HOME/run/DECISIONS.jsonl.lock" ] && mv "$SUVARNA_HOME/run/DECISIONS.jsonl.lock" "$SUVARNA_HOME/authority/"
  return 0
}

ns4_do_holds() {
  touch "$SUVARNA_HOME/authority/HOLDS.jsonl" "$SUVARNA_HOME/authority/HOLD_CLEARS.jsonl"
  chown Dev:suvarna-campaign "$SUVARNA_HOME/authority/HOLDS.jsonl"
  chmod 664 "$SUVARNA_HOME/authority/HOLDS.jsonl"
  chflags uappnd "$SUVARNA_HOME/authority/HOLDS.jsonl"
  chown Dev:staff "$SUVARNA_HOME/authority/HOLD_CLEARS.jsonl"
  chmod 644 "$SUVARNA_HOME/authority/HOLD_CLEARS.jsonl"
}

ns4_do_pgenv() {
  mkdir -p "/Users/suvarna/.config/suvarna/bin"
  chmod 700 "/Users/suvarna/.config/suvarna/bin"
  chown suvarna "/Users/suvarna/.config/suvarna" "/Users/suvarna/.config/suvarna/bin"
  [ -f "/Users/Dev/.config/suvarna/pgenv.sh" ] || return 1
  install -o suvarna -g staff -m 600 "/Users/Dev/.config/suvarna/pgenv.sh" "/Users/suvarna/.config/suvarna/pgenv.sh"
}

ns4_apply() {
  say "Setting folder ownership so the swarm can work in its own folders but never change yours..."
  if ! p_ns4_folders_ready; then
    do_or_sim "ns4_folders_ready" "NS.4" "create + chown/chmod/ACL campaign folders (swarm: hq/trunk/lanes/evidence/run/.repo; you: authority/config/control)" \
      -- ns4_do_folders || fail_step "NS.4" "could not set the campaign folders' ownership."
  else
    say "  Already done — folders are owned correctly."
  fi

  if p_ns4_decisions_moved; then
    say "  Decisions log already in authority/ (or nothing to move)."
  else
    do_or_sim "ns4_decisions_moved" "NS.4" "mv run/DECISIONS.jsonl(.lock) authority/" -- ns4_do_move_decisions \
      || fail_step "NS.4" "could not move the decisions log into authority/."
  fi

  if ! p_ns4_holds_ready; then
    do_or_sim "ns4_holds_ready" "NS.4" "create authority/HOLDS.jsonl (append-only) + authority/HOLD_CLEARS.jsonl" \
      -- ns4_do_holds || fail_step "NS.4" "could not prepare the hold-log files."
  fi

  if ! p_ns4_pgenv_ready; then
    do_or_sim "ns4_pgenv_ready" "NS.4" "install the read-only DB login into suvarna's own home (mode 600)" \
      -- ns4_do_pgenv || fail_step "NS.4" "could not give the swarm its own copy of the read-only database login."
  fi
  say "  Done."
}

ns4_verify() {
  if p_ns4_folders_ready; then add_verify "ns4_folders_owned_correctly" PASS; else add_verify "ns4_folders_owned_correctly" FAIL; fi
  if p_ns4_holds_ready; then add_verify "ns4_holds_log_ready" PASS; else add_verify "ns4_holds_log_ready" FAIL; fi
  if p_ns4_pgenv_ready; then add_verify "ns4_reader_login_installed" PASS; else add_verify "ns4_reader_login_installed" FAIL; fi
}

ns4_undo() {
  local rc=0
  if p_ns4_folders_ready || { [ "$SIMULATE" != "1" ] && [ -d "$SUVARNA_HOME/broker" ]; }; then
    do_or_sim "ns4_folders_ready=0" "UNDO" "chown -R \${SUDO_USER:-Dev}:staff the campaign folders (ownership/ACL only — no data deleted)" \
      -- ns4_undo_ownership || { say "  Could not fully restore folder ownership."; rc=1; }
  fi
  return $rc
}

ns4_undo_ownership() {
  local d owner
  owner="${SUDO_USER:-Dev}"
  for d in $NS4_SWARM_DIRS; do
    [ -e "$SUVARNA_HOME/$d" ] && chown -R "$owner:staff" "$SUVARNA_HOME/$d"
  done
  [ -e "$SUVARNA_HOME/broker" ] && chown -R "$owner:staff" "$SUVARNA_HOME/broker"
  return 0
}

# ---------------------------------------------------------------------------------------------
# NS.8 — always-on LaunchDaemons (only if the plist sources already exist)
# ---------------------------------------------------------------------------------------------
p_ns8_source_present() {  # $1 = short service name
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns8_source_present_$1"
  else [ -f "$LAUNCHD_SRC_DIR/com.marsys.suvarna.$1.plist" ]
  fi
}

p_ns8_installed() {  # $1 = short service name
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns8_installed_$1"
  else [ -f "$LAUNCHD_DIR/com.marsys.suvarna.$1.plist" ]
  fi
}

ns8_check() {
  local svc any_pending=0
  for svc in $NS8_SERVICES; do
    if p_ns8_source_present "$svc" && ! p_ns8_installed "$svc"; then any_pending=1; fi
  done
  if [ "$any_pending" = "1" ]; then
    say "[pending] NS.8 — would install the LaunchDaemons whose plist files already exist."
  else
    say "[done]    NS.8 — LaunchDaemons already installed, or their plist files do not exist yet (skipped)."
  fi
}

ns8_apply() {
  say "Installing the always-on services (only for the ones whose files are ready)..."
  local svc installed=0 skipped=0
  for svc in $NS8_SERVICES; do
    if p_ns8_installed "$svc"; then
      say "  '$svc' already installed."
      continue
    fi
    if ! p_ns8_source_present "$svc"; then
      say "  Skipping '$svc' — its plist has not been generated into the control checkout yet."
      skipped=$((skipped + 1))
      continue
    fi
    do_or_sim "ns8_installed_$svc" "NS.8" "install com.marsys.suvarna.$svc.plist to $LAUNCHD_DIR (root:wheel, 644) and bootstrap it" \
      -- ns8_install_one "$svc" \
      || fail_step "NS.8" "could not install the '$svc' service."
    installed=$((installed + 1))
  done
  if [ "$installed" -eq 0 ] && [ "$skipped" -gt 0 ]; then
    say "  Nothing installed yet — none of the plist files exist in the control checkout."
  elif [ "$installed" -gt 0 ]; then
    say "  Done — installed $installed service(s). They start idle until N-1 is recorded."
  fi
}

ns8_install_one() {
  local svc="$1"
  install -o root -g wheel -m 644 "$LAUNCHD_SRC_DIR/com.marsys.suvarna.$svc.plist" "$LAUNCHD_DIR/"
  launchctl bootstrap system "$LAUNCHD_DIR/com.marsys.suvarna.$svc.plist"
}

ns8_undo_one() {
  local svc="$1"
  launchctl bootout "system/com.marsys.suvarna.$svc" 2>/dev/null || true
  rm -f "$LAUNCHD_DIR/com.marsys.suvarna.$svc.plist"
}

ns8_verify() {
  local svc
  for svc in $NS8_SERVICES; do
    if [ "$SIMULATE" = "1" ]; then
      if sim_state_is_true "ns8_running_$svc"; then add_verify "ns8_running_$svc" PASS; else add_verify "ns8_running_$svc" FAIL; fi
    else
      if launchctl print "system/com.marsys.suvarna.$svc" 2>/dev/null | grep -q 'state = running'; then
        add_verify "ns8_running_$svc" PASS
      else
        add_verify "ns8_running_$svc" FAIL
      fi
    fi
  done
}

ns8_undo() {
  local svc rc=0
  for svc in $NS8_SERVICES; do
    if p_ns8_installed "$svc"; then
      do_or_sim "ns8_installed_$svc=0" "UNDO" "launchctl bootout + remove com.marsys.suvarna.$svc.plist" \
        -- ns8_undo_one "$svc" || { say "  Could not fully remove '$svc'."; rc=1; }
    fi
  done
  return $rc
}

# ---------------------------------------------------------------------------------------------
# NS.9 — power + software update settings
# ---------------------------------------------------------------------------------------------
p_ns9_power_ready() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns9_power_ready"
  else
    { pmset -g custom 2>/dev/null || true; } | awk '/^AC Power:/{f=1} f && / sleep /{print $2; exit}' | grep -qx 0 \
      && { pmset -g 2>/dev/null || true; } | grep -q 'autorestart *1'
  fi
}

p_ns9_softwareupdate_ready() {
  if [ "$SIMULATE" = "1" ]; then sim_state_is_true "ns9_softwareupdate_ready"
  else
    [ "$(defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates 2>/dev/null || echo 1)" = "0" ] \
      && [ "$(defaults read /Library/Preferences/com.apple.commerce AutoUpdateRestartRequired 2>/dev/null || echo 1)" = "0" ]
  fi
}

ns9_check() {
  if p_ns9_power_ready && p_ns9_softwareupdate_ready; then
    say "[done]    NS.9 — power and software-update settings already match the campaign's needs."
  else
    say "[pending] NS.9 — would keep the Mac awake on AC power and pause automatic macOS updates."
  fi
}

ns9_apply() {
  say "Setting power and update preferences for the campaign..."
  if ! p_ns9_power_ready; then
    do_or_sim "ns9_power_ready" "NS.9" "pmset -c sleep 0 disksleep 0; pmset -a autorestart 1" -- ns9_do_power \
      || fail_step "NS.9" "could not change the power settings."
  fi
  if ! p_ns9_softwareupdate_ready; then
    do_or_sim "ns9_softwareupdate_ready" "NS.9" "defaults write .../SoftwareUpdate AutomaticallyInstallMacOSUpdates=0; .../commerce AutoUpdateRestartRequired=0" \
      -- ns9_do_softwareupdate || fail_step "NS.9" "could not change the software-update settings."
  fi
  say "  Done — the Mac stays awake on AC power and won't auto-restart for an update mid-campaign."
}

ns9_do_power() {
  pmset -c sleep 0 disksleep 0
  pmset -a autorestart 1
}

ns9_do_softwareupdate() {
  defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool false
  defaults write /Library/Preferences/com.apple.commerce AutoUpdateRestartRequired -bool false
}

ns9_verify() {
  if p_ns9_power_ready; then add_verify "ns9_power_settings" PASS; else add_verify "ns9_power_settings" FAIL; fi
  if p_ns9_softwareupdate_ready; then add_verify "ns9_softwareupdate_settings" PASS; else add_verify "ns9_softwareupdate_settings" FAIL; fi
}
# NS.9 is a machine-wide preference, not an owner/ACL/account this script created — --undo
# intentionally leaves it as-is (nothing here is reversed by design; see the setup guide appendix).

# ---------------------------------------------------------------------------------------------
# NS.5 / NS.7 — interactive browser-dependent helpers
# ---------------------------------------------------------------------------------------------
mode_github_token() {
  cat <<'EOF'
Before you continue, do this in a browser (a few clicks — takes about 5 minutes):
  1. In a private/incognito window, sign in to github.com as a NEW account for the swarm
     (for example "marsys-suvarna-bot"), using a second email address. Turn on two-factor
     authentication for it.
  2. As yourself (the Marsys-Technologies org owner), give that account Write access to the
     Madhav repository (not Maintain, not Admin) and accept the invitation in the bot's window.
  3. Still signed in as the bot: Settings -> Developer settings -> Personal access tokens ->
     Fine-grained tokens -> Generate new token.
       - Resource owner: Marsys-Technologies
       - Repository access: Only select repositories -> Madhav
       - Expiration: 90 days
       - Permissions: Contents (Read and write), Pull requests (Read and write), Metadata (Read),
         Commit statuses (Read), Checks (Read), Actions (Read). Everything else: No access.
  4. Copy the token now — GitHub will not show it to you again.

When you have the token copied, come back to this window.
EOF
  printf 'Paste the token now (it will not be shown on screen), then press Enter: '
  local token
  if [ "$SIMULATE" = "1" ]; then IFS= read -r token; else IFS= read -rs token; printf '\n'; fi
  if [ -z "$token" ]; then say "No token entered — nothing was done."; return 1; fi

  say "Handing the token to the 'suvarna' account (it is never written to a file you keep)..."
  if [ "$SIMULATE" = "1" ]; then
    printf 'gh auth login --hostname github.com --git-protocol https --with-token (token piped via stdin, not logged)\n' >> "$SIM_LOG"
    printf 'gh auth setup-git\n' >> "$SIM_LOG"
    printf 'git config --global user.name "Suvarna swarm"\n' >> "$SIM_LOG"
    printf 'git config --global user.email "marsys-suvarna-bot@users.noreply.github.com"\n' >> "$SIM_LOG"
    sim_state_set "ns5_github_token_set" 1
  else
    printf '%s' "$token" | sudo -iu suvarna gh auth login --hostname github.com --git-protocol https --with-token
    sudo -iu suvarna gh auth setup-git
    sudo -iu suvarna git config --global user.name "Suvarna swarm"
    sudo -iu suvarna git config --global user.email "marsys-suvarna-bot@users.noreply.github.com"
  fi
  unset token

  say "Verifying..."
  if [ "$SIMULATE" = "1" ]; then
    say "  (simulated) gh auth status -> logged in as marsys-suvarna-bot"
  else
    sudo -iu suvarna gh auth status
  fi
}

mode_claude_token() {
  cat <<'EOF'
Before you continue:
  1. This step installs the swarm's own copy of Claude Code, if it is not already there.
  2. A browser link will appear below. Open it and sign in with your Claude subscription account.
  3. The tool will then print a token in this terminal. Copy it.
EOF
  say "Installing the swarm's copy of Claude Code (skipped if already installed)..."
  if [ "$SIMULATE" = "1" ]; then
    if sim_state_is_true "ns7_claude_installed"; then
      say "  Already done."
    else
      printf 'curl -fsSL https://claude.ai/install.sh | bash -s 2.1.239 (as suvarna)\n' >> "$SIM_LOG"
      sim_state_set "ns7_claude_installed" 1
    fi
  else
    if [ -x /Users/suvarna/.local/bin/claude ]; then
      say "  Already done."
    else
      sudo -iu suvarna sh -c 'curl -fsSL https://claude.ai/install.sh | bash -s 2.1.239'
    fi
  fi

  say "Starting the login flow — follow the link that appears, then copy the token it prints..."
  if [ "$SIMULATE" = "1" ]; then
    printf 'claude setup-token (as suvarna; prints a browser link, then a token)\n' >> "$SIM_LOG"
  else
    sudo -iu suvarna /Users/suvarna/.local/bin/claude setup-token
  fi

  printf 'Paste the token now (it will not be shown on screen), then press Enter: '
  local token
  if [ "$SIMULATE" = "1" ]; then IFS= read -r token; else IFS= read -rs token; printf '\n'; fi
  if [ -z "$token" ]; then say "No token entered — nothing was done."; return 1; fi

  if [ "$SIMULATE" = "1" ]; then
    printf 'write CLAUDE_CODE_OAUTH_TOKEN=<redacted> to ~suvarna/.config/suvarna/claude_oauth.env (mode 600, via stdin, not logged)\n' >> "$SIM_LOG"
    sim_state_set "ns7_token_set" 1
  else
    printf 'CLAUDE_CODE_OAUTH_TOKEN=%s' "$token" | sudo -iu suvarna sh -c 'umask 077; cat > ~/.config/suvarna/claude_oauth.env'
  fi
  unset token

  say "Verifying with a no-op pass..."
  if [ "$SIMULATE" = "1" ]; then
    say "  (simulated) claude -p \"reply OK\" -> OK"
  else
    sudo -iu suvarna claude -p "reply OK" --settings /Users/Dev/suvarna/config/claude-settings.json --permission-mode dontAsk
  fi
}

# ---------------------------------------------------------------------------------------------
# --verify: JSON output
# ---------------------------------------------------------------------------------------------
VERIFY_RESULTS=()
add_verify() { VERIFY_RESULTS+=("$1:$2"); }

write_verify_json() {
  mkdir -p "$(dirname "$VERIFY_OUT")" 2>/dev/null || true
  local n i pair k v line
  n=${#VERIFY_RESULTS[@]}
  {
    printf '{\n'
    i=0
    for pair in "${VERIFY_RESULTS[@]:-}"; do
      [ -z "$pair" ] && continue
      k="${pair%%:*}"; v="${pair#*:}"
      i=$((i + 1))
      if [ "$i" -lt "$n" ]; then line=","; else line=""; fi
      printf '  "%s": "%s"%s\n' "$k" "$v" "$line"
    done
    printf '}\n'
  } > "$VERIFY_OUT"
  say "Wrote $VERIFY_OUT"
}

run_verify_mode() {
  require_root_or_sim
  say "Running every post-setup check..."
  ns1_verify; ns2_verify; ns3_verify; ns4_verify; ns8_verify; ns9_verify
  write_verify_json
  local pair fails=0
  for pair in "${VERIFY_RESULTS[@]:-}"; do
    [ -z "$pair" ] && continue
    case "$pair" in *:FAIL) fails=$((fails + 1)) ;; esac
  done
  if [ "$fails" -eq 0 ]; then
    say "All checks PASS."
  else
    say "$fails check(s) FAILED — see $VERIFY_OUT for which ones, and re-run --apply."
  fi
}

# ---------------------------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------------------------
require_root_or_sim() {
  if [ "$SIMULATE" = "1" ]; then
    if [ "$SIM_ROOT" != "1" ]; then
      say "This mode must be run with sudo (as root)."
      exit 1
    fi
    return 0
  fi
  if [ "$(id -u)" != "0" ]; then
    say "This mode must be run with sudo: sudo bash $SCRIPT_PATH --$MODE"
    exit 1
  fi
}

guard_admin_and_home() {
  if [ "$SIMULATE" = "1" ]; then
    if ! sim_state_is_true "admin_check_pass"; then
      say "Refusing to run: the account that invoked sudo is not an administrator."
      exit 1
    fi
    if ! sim_state_is_true "suvarna_home_exists"; then
      say "Refusing to run: $SUVARNA_HOME does not exist yet."
      exit 1
    fi
    return 0
  fi
  local invoking="${SUDO_USER:-}"
  if [ -z "$invoking" ]; then
    say "Refusing to run: could not tell who invoked sudo (SUDO_USER is empty)."
    exit 1
  fi
  if ! dseditgroup -o checkmember -m "$invoking" admin >/dev/null 2>&1; then
    say "Refusing to run: '$invoking' is not an administrator on this Mac."
    exit 1
  fi
  if [ ! -d "$SUVARNA_HOME" ]; then
    say "Refusing to run: $SUVARNA_HOME does not exist yet. Ask Strategic Suvarna to run NS.0 first."
    exit 1
  fi
}

# ---------------------------------------------------------------------------------------------
# Top-level modes
# ---------------------------------------------------------------------------------------------
run_check_mode() {
  say "Checking what is already done (this changes nothing)..."
  ns1_check; ns2_check; ns3_check; ns4_check; ns8_check; ns9_check
  say ""
  say "Run 'sudo bash $SCRIPT_PATH --apply' to do whatever is still pending."
}

run_apply_mode() {
  require_root_or_sim
  guard_admin_and_home
  ns1_apply
  ns2_apply
  ns3_apply
  ns4_apply
  ns8_apply
  ns9_apply
  say ""
  say "Setup steps complete. Run: sudo bash $SCRIPT_PATH --verify   to confirm everything passes."
}

run_undo_mode() {
  require_root_or_sim
  local rc=0
  say "Undo: stopping and removing the always-on services..."
  ns8_undo || rc=1
  say "Undo: removing the sudo rule and the build broker account..."
  ns2_undo || rc=1
  say "Undo: returning folder ownership to you..."
  ns4_undo || rc=1
  say "Undo: removing the swarm's macOS user and campaign group..."
  ns1_undo || rc=1
  if [ "$rc" -eq 0 ]; then
    say "Undo complete. Nothing under $SUVARNA_HOME was deleted — only ownership changed back to you."
    say "Your own credential files (locked by NS.3) were left locked; that tightening is not reversed."
  else
    say "Undo finished, but some steps could not complete — see the messages above."
  fi
  return $rc
}

print_help() {
  sed -n '2,26p' "$SCRIPT_PATH"
}

parse_args() {
  MODE=""
  local arg
  for arg in "$@"; do
    case "$arg" in
      --check) MODE="check" ;;
      --apply) MODE="apply" ;;
      --undo) MODE="undo" ;;
      --verify) MODE="verify" ;;
      --github-token) MODE="github-token" ;;
      --claude-token) MODE="claude-token" ;;
      -h|--help) MODE="help" ;;
      *) echo "Unknown option: $arg" >&2; exit 2 ;;
    esac
  done
  if [ -z "$MODE" ]; then
    if is_running_as_root; then
      echo "Running as root: choose a mode explicitly (--check, --apply, --undo or --verify)." >&2
      exit 2
    fi
    MODE="check"
  fi
}

main() {
  parse_args "$@"
  if [ "$MODE" != "help" ]; then
    say "native_setup.sh v$SCRIPT_VERSION — mode: $MODE"
  fi
  case "$MODE" in
    help) print_help ;;
    check) run_check_mode ;;
    apply) run_apply_mode ;;
    undo) run_undo_mode ;;
    verify) run_verify_mode ;;
    github-token) require_root_or_sim; mode_github_token ;;
    claude-token) require_root_or_sim; mode_claude_token ;;
  esac
}

main "$@"
